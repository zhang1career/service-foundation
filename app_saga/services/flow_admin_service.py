from __future__ import annotations

from django.db import transaction

from app_saga.models import SagaFlow, SagaFlowStep


def list_all_flows():
    return list(
        SagaFlow.objects.using("saga_rw")
        .select_related("participant")
        .order_by("id")
    )


def list_flows_for_participant(participant_id: int):
    return list(
        SagaFlow.objects.using("saga_rw")
        .filter(participant_id=participant_id)
        .order_by("id")
    )


def get_flow(flow_id: int) -> SagaFlow | None:
    return (
        SagaFlow.objects.using("saga_rw")
        .select_related("participant")
        .filter(pk=flow_id)
        .first()
    )


@transaction.atomic(using="saga_rw")
def create_flow(*, participant_id: int, name: str, status: int) -> SagaFlow:
    f = SagaFlow(
        participant_id=participant_id,
        name=(name or "").strip(),
        status=int(status),
    )
    f.save(using="saga_rw")
    return f


@transaction.atomic(using="saga_rw")
def update_flow(flow_id: int, *, name: str | None = None, status: int | None = None):
    f = SagaFlow.objects.using("saga_rw").filter(pk=flow_id).first()
    if not f:
        return None
    if name is not None:
        f.name = name.strip()
    if status is not None:
        f.status = int(status)
    f.save(using="saga_rw")
    return f


@transaction.atomic(using="saga_rw")
def delete_flow(flow_id: int) -> bool:
    deleted, _ = SagaFlow.objects.using("saga_rw").filter(pk=flow_id).delete()
    return deleted > 0


def list_steps_for_flow(flow_id: int):
    return list(
        SagaFlowStep.objects.using("saga_rw")
        .filter(flow_id=flow_id)
        .order_by("step_index", "id")
    )


@transaction.atomic(using="saga_rw")
def create_flow_step(
        *,
        flow_id: int,
        name: str,
        action_url: str,
        compensate_url: str,
        timeout_sec: int = 30,
        max_retries: int = 10,
        is_need_confirm: int = 0,
) -> SagaFlowStep:
    ncf = int(is_need_confirm)
    if ncf not in (0, 1):
        raise ValueError("is_need_confirm must be 0 or 1")
    brs = list_steps_for_flow(flow_id)
    mx = max((b.step_index for b in brs), default=-1)
    next_idx = mx + 1
    s = SagaFlowStep(
        flow_id=flow_id,
        step_index=next_idx,
        name=(name or "").strip(),
        action_url=(action_url or "").strip(),
        compensate_url=(compensate_url or "").strip(),
        timeout_sec=int(timeout_sec),
        max_retries=int(max_retries),
        is_need_confirm=ncf,
    )
    s.save(using="saga_rw")
    return s


@transaction.atomic(using="saga_rw")
def update_flow_step(
        step_id: int,
        *,
        name: str | None = None,
        action_url: str | None = None,
        compensate_url: str | None = None,
        timeout_sec: int | None = None,
        max_retries: int | None = None,
        is_need_confirm: int | None = None,
):
    s = SagaFlowStep.objects.using("saga_rw").filter(pk=step_id).first()
    if not s:
        return None
    if name is not None:
        s.name = name.strip()
    if action_url is not None:
        s.action_url = action_url.strip()
    if compensate_url is not None:
        s.compensate_url = compensate_url.strip()
    if timeout_sec is not None:
        s.timeout_sec = int(timeout_sec)
    if max_retries is not None:
        s.max_retries = int(max_retries)
    if is_need_confirm is not None:
        ncf = int(is_need_confirm)
        if ncf not in (0, 1):
            raise ValueError("is_need_confirm must be 0 or 1")
        s.is_need_confirm = ncf
    s.save(using="saga_rw")
    return s


@transaction.atomic(using="saga_rw")
def delete_flow_step(step_id: int) -> bool:
    deleted, _ = SagaFlowStep.objects.using("saga_rw").filter(pk=step_id).delete()
    return deleted > 0


@transaction.atomic(using="saga_rw")
def reorder_flow_steps(flow_id: int, ordered_step_ids: list[int]):
    """Set ``step_index`` to ``0..n-1`` in the given order (same ids as DB for this flow)."""
    rows = list(
        SagaFlowStep.objects.using("saga_rw")
        .filter(flow_id=flow_id)
        .order_by("step_index", "id")
    )
    id_set = {r.id for r in rows}
    if not ordered_step_ids:
        raise ValueError("ordered_step_ids is required")
    if len(ordered_step_ids) != len(id_set):
        raise ValueError("step order length mismatch")
    if set(ordered_step_ids) != id_set:
        raise ValueError("step order id set mismatch")
    base = max((r.step_index for r in rows), default=0) + 100000
    id_to_row = {r.id: r for r in rows}
    for i, sid in enumerate(ordered_step_ids):
        r = id_to_row[sid]
        r.step_index = base + i
        r.save(using="saga_rw", update_fields=["step_index", "ut"])
    for i, sid in enumerate(ordered_step_ids):
        r = id_to_row[sid]
        r.step_index = i
        r.save(using="saga_rw", update_fields=["step_index", "ut"])
