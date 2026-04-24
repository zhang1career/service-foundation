from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import transaction

from app_saga.enums import (
    SagaInstanceStatus,
    SagaStepActionStatus,
    SagaStepCompensateStatus,
)
from app_saga.models import SagaFlow, SagaFlowStep, SagaInstance, SagaStepRun
from app_saga.services import outbound_http
from app_saga.services.snowflake_id import SnowflakeIdError, allocate_snowflake_int
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.date_util import get_now_timestamp_ms


def _ordered_steps(flow_id: int) -> list[SagaFlowStep]:
    return list(
        SagaFlowStep.objects.using("saga_rw")
        .filter(flow_id=flow_id)
        .order_by("step_index", "id")
    )


def _now_ms() -> int:
    return get_now_timestamp_ms()


def _backoff_ms(retry_count: int) -> int:
    base = int(settings.SAGA_SCAN_BACKOFF_BASE_MS)
    step = int(settings.SAGA_SCAN_BACKOFF_STEP_MS)
    cap = int(settings.SAGA_SCAN_BACKOFF_CAP_MS)
    return min(cap, base + retry_count * step)


def _next_retry_capped(now_ms: int) -> int:
    cap_ms = int(settings.SAGA_SCAN_NEXT_RETRY_CAP_MS)
    return now_ms + cap_ms


def _payload_for_step(step: SagaFlowStep, payloads: dict[str, Any]) -> dict[str, Any]:
    k_idx = str(step.step_index)
    v = payloads.get(k_idx)
    if isinstance(v, dict):
        return v
    name = (step.name or "").strip()
    if name:
        v2 = payloads.get(name)
        if isinstance(v2, dict):
            return v2
    return {}


def _load_start_request(inst: SagaInstance) -> dict[str, Any]:
    """JSON snapshot of POST /api/saga/instances at creation (`instance.start_body`)."""
    raw = getattr(inst, "start_body", None)
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        return outbound_http.loads_json_dict(raw)
    except ValueError:
        return {}


def serialize_instance(inst: SagaInstance) -> dict[str, Any]:
    runs = list(
        inst.step_runs.order_by("step_index").values(
            "step_index",
            "action_status",
            "compensate_status",
            "last_http_status_action",
            "last_http_status_compensate",
            "last_error_action",
            "last_error_compensate",
        )
    )
    return {
        "saga_instance_id": str(inst.pk),
        "idem_key": inst.idem_key,
        "flow_id": inst.flow_id,
        "status": inst.status,
        "current_step_index": inst.current_step_index,
        "retry_count": inst.retry_count,
        "last_error": (inst.last_error or "")[:500],
        "context": outbound_http.loads_json_dict(inst.context),
        "step_runs": runs,
    }


def get_instance_by_id(pk: int) -> SagaInstance | None:
    return (
        SagaInstance.objects.using("saga_rw")
        .select_related("flow", "participant")
        .filter(pk=pk)
        .first()
    )


def get_instance_by_idem(idem_key: int) -> SagaInstance | None:
    return (
        SagaInstance.objects.using("saga_rw")
        .select_related("flow", "participant")
        .filter(idem_key=idem_key)
        .first()
    )


def start_instance(
        *,
        access_key: str,
        flow_id: int,
        context: dict[str, Any] | None,
        idem_key: int | None,
        step_payloads: dict[str, Any] | None,
) -> dict[str, Any]:
    from app_saga.services import participant_reg_service

    p = participant_reg_service.get_participant_by_access_key(access_key)
    if not p or p.status != ServiceRegStatus.ENABLED.value:
        raise ValueError("invalid or disabled access_key")
    try:
        fid = int(flow_id)
    except (TypeError, ValueError):
        raise ValueError("flow_id must be int") from None
    if fid <= 0:
        raise ValueError("flow_id must be positive")
    flow = (
        SagaFlow.objects.using("saga_rw")
        .filter(pk=fid, participant_id=p.pk)
        .first()
    )
    if not flow or flow.status != ServiceRegStatus.ENABLED.value:
        raise ValueError("unknown or disabled flow_id for this access_key")
    steps = _ordered_steps(flow.pk)
    if not steps:
        raise ValueError("flow has no steps")

    ctx = context if isinstance(context, dict) else {}
    payloads = step_payloads if isinstance(step_payloads, dict) else {}

    if idem_key is not None:
        ik = int(idem_key)
        existing = get_instance_by_idem(ik)
        if existing:
            return serialize_instance(existing)
    else:
        try:
            ik = allocate_snowflake_int()
        except SnowflakeIdError as e:
            raise ValueError(str(e)) from e

    start_request: dict[str, Any] = {
        "access_key": access_key.strip(),
        "flow_id": int(flow.pk),
        "context": ctx,
        "step_payloads": payloads,
        "idem_key": int(ik),
    }
    now = _now_ms()
    with transaction.atomic(using="saga_rw"):
        inst = SagaInstance(
            flow_id=flow.pk,
            participant_id=p.pk,
            status=SagaInstanceStatus.RUNNING,
            idem_key=ik,
            context=outbound_http.dumps_json(ctx),
            step_payloads=outbound_http.dumps_json(payloads),
            start_body=outbound_http.dumps_json(start_request),
            current_step_index=0,
            next_retry_at=now,
            retry_count=0,
            last_error="",
        )
        inst.save(using="saga_rw")
        for st in steps:
            sr = SagaStepRun(
                instance_id=inst.pk,
                flow_step_id=st.pk,
                step_index=st.step_index,
                action_status=SagaStepActionStatus.PENDING,
                compensate_status=SagaStepCompensateStatus.PENDING,
                last_error_action="",
                last_error_compensate="",
            )
            sr.save(using="saga_rw")

    budget = int(settings.SAGA_START_SYNC_STEP_BUDGET)
    for _ in range(budget):
        process_instance(inst.pk)
        inst = get_instance_by_id(inst.pk)
        if not inst:
            break
        if inst.status in (
                SagaInstanceStatus.COMPLETED,
                SagaInstanceStatus.ROLLED_BACK,
                SagaInstanceStatus.FAILED,
        ):
            break
        if inst.next_retry_at > _now_ms():
            break

    inst = get_instance_by_id(inst.pk)
    return serialize_instance(inst) if inst else {}


def _run_forward_action(
        *,
        inst: SagaInstance,
        fs: SagaFlowStep,
        sr: SagaStepRun,
        ctx: dict[str, Any],
        payloads: dict[str, Any],
) -> bool:
    body = {
        "saga_instance_id": str(inst.pk),
        "idem_key": inst.idem_key,
        "flow_id": inst.flow_id,
        "step_index": fs.step_index,
        "phase": "action",
        "context": ctx,
        "payload": _payload_for_step(fs, payloads),
        "start_request": _load_start_request(inst),
    }
    st, err, resp_obj = outbound_http.call_saga_endpoint(
        url=fs.action_url,
        json_body=body,
        timeout_sec=float(fs.timeout_sec),
    )
    sr.last_http_status_action = st if st else None
    sr.last_error_action = err
    ok = (200 <= st < 300) and not err
    if ok:
        outbound_http.merge_context_from_response(ctx, resp_obj)
    sr.action_status = (
        SagaStepActionStatus.SUCCEEDED if ok else SagaStepActionStatus.PENDING
    )
    sr.save(
        using="saga_rw",
        update_fields=[
            "last_http_status_action",
            "last_error_action",
            "action_status",
            "ut",
        ],
    )
    return ok


def _run_compensate(
        *,
        inst: SagaInstance,
        fs: SagaFlowStep,
        sr: SagaStepRun,
        ctx: dict[str, Any],
        payloads: dict[str, Any],
) -> bool:
    body = {
        "saga_instance_id": str(inst.pk),
        "idem_key": inst.idem_key,
        "flow_id": inst.flow_id,
        "step_index": fs.step_index,
        "phase": "compensate",
        "context": ctx,
        "payload": _payload_for_step(fs, payloads),
        "start_request": _load_start_request(inst),
    }
    st, err, _resp = outbound_http.call_saga_endpoint(
        url=fs.compensate_url,
        json_body=body,
        timeout_sec=float(fs.timeout_sec),
    )
    sr.last_http_status_compensate = st if st else None
    sr.last_error_compensate = err
    ok = (200 <= st < 300) and not err
    sr.compensate_status = (
        SagaStepCompensateStatus.SUCCEEDED if ok else SagaStepCompensateStatus.PENDING
    )
    sr.save(
        using="saga_rw",
        update_fields=[
            "last_http_status_compensate",
            "last_error_compensate",
            "compensate_status",
            "ut",
        ],
    )
    return ok


def process_instance(instance_pk: int) -> None:
    now = _now_ms()
    with transaction.atomic(using="saga_rw"):
        inst = (
            SagaInstance.objects.using("saga_rw")
            .select_for_update()
            .select_related("flow")
            .filter(pk=instance_pk)
            .first()
        )
        if not inst:
            return
        if inst.status in (
                SagaInstanceStatus.COMPLETED,
                SagaInstanceStatus.ROLLED_BACK,
                SagaInstanceStatus.FAILED,
        ):
            return
        if inst.next_retry_at > now:
            return

        steps = _ordered_steps(inst.flow_id)
        n = len(steps)
        ctx = outbound_http.loads_json_dict(inst.context)
        payloads = outbound_http.loads_json_dict(inst.step_payloads)

        if inst.status == SagaInstanceStatus.RUNNING:
            if inst.current_step_index >= n:
                inst.status = SagaInstanceStatus.COMPLETED
                inst.last_error = ""
                inst.next_retry_at = now
                inst.save(
                    using="saga_rw",
                    update_fields=["status", "last_error", "next_retry_at", "ut"],
                )
                return

            step_idx = inst.current_step_index
            sr = (
                SagaStepRun.objects.using("saga_rw")
                .select_for_update()
                .filter(instance_id=inst.pk, step_index=step_idx)
                .first()
            )
            fs = next((s for s in steps if s.step_index == step_idx), None)
            if not sr or not fs:
                inst.status = SagaInstanceStatus.FAILED
                inst.last_error = "step run or definition missing"
                inst.next_retry_at = _next_retry_capped(now)
                inst.save(
                    using="saga_rw",
                    update_fields=["status", "last_error", "next_retry_at", "ut"],
                )
                return

            ok = _run_forward_action(inst=inst, fs=fs, sr=sr, ctx=ctx, payloads=payloads)
            if ok:
                inst.context = outbound_http.dumps_json(ctx)
                inst.current_step_index = step_idx + 1
                inst.retry_count = 0
                inst.last_error = ""
                if inst.current_step_index >= n:
                    inst.status = SagaInstanceStatus.COMPLETED
                inst.next_retry_at = now
                inst.save(
                    using="saga_rw",
                    update_fields=[
                        "context",
                        "current_step_index",
                        "retry_count",
                        "last_error",
                        "status",
                        "next_retry_at",
                        "ut",
                    ],
                )
            else:
                inst.retry_count += 1
                max_r = int(fs.max_retries)
                if inst.retry_count <= max_r:
                    inst.last_error = sr.last_error_action[:2000] if sr.last_error_action else ""
                    inst.next_retry_at = now + _backoff_ms(inst.retry_count)
                    inst.save(
                        using="saga_rw",
                        update_fields=["retry_count", "last_error", "next_retry_at", "ut"],
                    )
                else:
                    sr.action_status = SagaStepActionStatus.FAILED
                    sr.save(
                        using="saga_rw",
                        update_fields=["action_status", "ut"],
                    )
                    inst.status = SagaInstanceStatus.COMPENSATING
                    inst.retry_count = 0
                    inst.last_error = (sr.last_error_action or "")[:2000]
                    inst.next_retry_at = now
                    inst.save(
                        using="saga_rw",
                        update_fields=[
                            "status",
                            "retry_count",
                            "last_error",
                            "next_retry_at",
                            "ut",
                        ],
                    )
            return

        if inst.status == SagaInstanceStatus.COMPENSATING:
            cand = list(
                SagaStepRun.objects.using("saga_rw")
                .select_for_update()
                .filter(
                    instance_id=inst.pk,
                    action_status=SagaStepActionStatus.SUCCEEDED,
                    compensate_status=SagaStepCompensateStatus.PENDING,
                )
                .order_by("-step_index")
            )
            if not cand:
                inst.status = SagaInstanceStatus.ROLLED_BACK
                inst.last_error = ""
                inst.next_retry_at = now
                inst.save(
                    using="saga_rw",
                    update_fields=["status", "last_error", "next_retry_at", "ut"],
                )
                return

            sr = cand[0]
            fs = (
                SagaFlowStep.objects.using("saga_rw")
                .filter(pk=sr.flow_step_id)
                .first()
            )
            if not fs:
                inst.status = SagaInstanceStatus.FAILED
                inst.last_error = "flow step missing for compensate"
                inst.next_retry_at = _next_retry_capped(now)
                inst.save(
                    using="saga_rw",
                    update_fields=["status", "last_error", "next_retry_at", "ut"],
                )
                return

            ok = _run_compensate(inst=inst, fs=fs, sr=sr, ctx=ctx, payloads=payloads)
            if ok:
                inst.context = outbound_http.dumps_json(ctx)
                inst.retry_count = 0
                inst.last_error = ""
                inst.next_retry_at = now
                inst.save(
                    using="saga_rw",
                    update_fields=[
                        "context",
                        "retry_count",
                        "last_error",
                        "next_retry_at",
                        "ut",
                    ],
                )
            else:
                inst.retry_count += 1
                max_r = int(fs.max_retries)
                if inst.retry_count <= max_r:
                    inst.last_error = (sr.last_error_compensate or "")[:2000]
                    inst.next_retry_at = now + _backoff_ms(inst.retry_count)
                    inst.save(
                        using="saga_rw",
                        update_fields=["retry_count", "last_error", "next_retry_at", "ut"],
                    )
                else:
                    sr.compensate_status = SagaStepCompensateStatus.FAILED
                    sr.save(
                        using="saga_rw",
                        update_fields=["compensate_status", "ut"],
                    )
                    inst.status = SagaInstanceStatus.FAILED
                    inst.last_error = (sr.last_error_compensate or "compensate failed")[:2000]
                    inst.next_retry_at = _next_retry_capped(now)
                    inst.save(
                        using="saga_rw",
                        update_fields=["status", "last_error", "next_retry_at", "ut"],
                    )
