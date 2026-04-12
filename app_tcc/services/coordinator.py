from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import transaction

from app_tcc.enums import BranchStatus, GlobalTxStatus
from app_tcc.models import TccBranch, TccBranchMeta, TccGlobalTransaction, TccManualReview
from app_tcc.services import participant_http
from app_tcc.services.biz_branch_service import load_branch_metas_for_begin
from app_tcc.services.snowflake_id import allocate_snowflake_int
from common.utils.date_util import get_now_timestamp_ms


def _try_phase_timeout_delta() -> timedelta:
    sec = int(settings.TCC_PHASE_TRY_TIMEOUT_SECONDS)
    return timedelta(seconds=sec)


def confirm_phase_timeout_delta(branch_count: int) -> timedelta:
    sec = int(settings.TCC_PHASE_CONFIRM_TIMEOUT_SECONDS)
    return timedelta(seconds=max(1, branch_count) * sec)


def cancel_phase_timeout_delta(branch_count: int) -> timedelta:
    sec = int(settings.TCC_PHASE_CANCEL_TIMEOUT_SECONDS)
    return timedelta(seconds=max(1, branch_count) * sec)


def _await_confirm_delta() -> timedelta:
    sec = int(settings.TCC_AWAIT_CONFIRM_TIMEOUT_SECONDS)
    return timedelta(seconds=sec)


def _default_auto_confirm() -> bool:
    return bool(settings.TCC_DEFAULT_AUTO_CONFIRM)


def _plus_ms(base_ms: int, delta: timedelta) -> int:
    return base_ms + int(delta.total_seconds() * 1000)


def _participant_idem_key(b: TccBranch) -> str:
    return str(b.idem_key)


def _branch_payload_dict(b: TccBranch) -> dict[str, Any]:
    raw = (b.payload or "").strip() or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _call_participant_and_persist_branch(
    *,
    g: TccGlobalTransaction,
    b: TccBranch,
    url: str,
    phase: str,
    status_on_success: int,
    status_on_failure: int,
) -> tuple[int, str]:
    st, err = participant_http.call_participant(
        url=url,
        phase=phase,
        global_tx_id=str(g.pk),
        branch_id=str(b.pk),
        idempotency_key=_participant_idem_key(b),
        payload=_branch_payload_dict(b),
    )
    with transaction.atomic(using="tcc_rw"):
        b.refresh_from_db()
        b.last_http_status = st if st else None
        b.last_error = err
        if participant_http.is_success_status(st):
            b.status = status_on_success
        else:
            b.status = status_on_failure
        b.save(using="tcc_rw", update_fields=["last_http_status", "last_error", "status", "ut"])
    return st, err


def _invoke_participant_phase_or_mark_manual(
    *,
    g: TccGlobalTransaction,
    b: TccBranch,
    url: str,
    phase: str,
    status_on_success: int,
    status_on_failure: int,
    manual_reason: str,
) -> bool:
    st, err = _call_participant_and_persist_branch(
        g=g,
        b=b,
        url=url,
        phase=phase,
        status_on_success=status_on_success,
        status_on_failure=status_on_failure,
    )
    if participant_http.is_success_status(st):
        return True
    g.refresh_from_db()
    mark_manual_simple(
        g,
        manual_reason,
        {"branch_index": b.branch_index, "http": st, "err": err[:200]},
    )
    return False


def serialize_transaction(g: TccGlobalTransaction) -> dict[str, Any]:
    branches = list(
        g.branches.select_related("branch_meta").order_by("branch_index")
    )
    out: dict[str, Any] = {
        "global_tx_id": str(g.pk),
        "idem_key": g.idem_key,
        "status": g.status,
        "auto_confirm": g.auto_confirm,
        "retry_count": g.retry_count,
        "branches": [
            {
                "branch_id": str(b.pk),
                "branch_meta_id": b.branch_meta_id,
                "branch_index": b.branch_index,
                "branch_status": b.status,
                "last_http_status": b.last_http_status,
                "last_error": (b.last_error or "")[:200],
            }
            for b in branches
        ],
    }
    mr = TccManualReview.objects.using("tcc_rw").filter(global_tx_id=g.pk).first()
    if mr:
        out["review_snapshot"] = mr.snapshot
    return out


def get_transaction_by_global_id(global_tx_id: str) -> TccGlobalTransaction | None:
    s = (global_tx_id or "").strip()
    if not s:
        return None
    try:
        pk = int(s)
    except ValueError:
        return None
    return TccGlobalTransaction.objects.using("tcc_rw").filter(pk=pk).first()


def get_transaction_for_query(
    *,
    global_tx_id: str | None = None,
    idem_key: int | None = None,
) -> TccGlobalTransaction | None:
    if idem_key is not None:
        return (
            TccGlobalTransaction.objects.using("tcc_rw")
            .filter(idem_key=idem_key)
            .first()
        )
    if global_tx_id:
        return get_transaction_by_global_id(global_tx_id)
    return None


def begin_transaction(
    *,
    branch_items: list[dict[str, Any]],
    auto_confirm: bool | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not branch_items:
        raise ValueError("branch_items is required")

    payloads: dict[int, dict[str, Any]] = {}
    for raw in branch_items:
        mid = raw.get("branch_meta_id")
        if not isinstance(mid, int):
            raise ValueError("branch_meta_id is required and must be int")
        if mid in payloads:
            raise ValueError("duplicate branch_meta_id in branch_items")
        payload = raw.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("branch payload must be a JSON object when provided")
        payloads[mid] = payload or {}

    ordered_metas = load_branch_metas_for_begin(list(payloads.keys()))

    if auto_confirm is None:
        auto_confirm = _default_auto_confirm()

    n = len(ordered_metas)
    snow_ids = [allocate_snowflake_int() for _ in range(1 + n)]
    tx_idem = snow_ids[0]
    pending: list[tuple[TccBranchMeta, dict[str, Any], int]] = [
        (meta, payloads[meta.pk], snow_ids[i + 1])
        for i, meta in enumerate(ordered_metas)
    ]

    now_ms = get_now_timestamp_ms()
    phase_deadline_ms = _plus_ms(
        now_ms,
        _try_phase_timeout_delta() * max(1, len(pending)),
    )

    with transaction.atomic(using="tcc_rw"):
        g = TccGlobalTransaction.objects.create(
            status=GlobalTxStatus.TRYING,
            phase_started_at=now_ms,
            phase_deadline_at=phase_deadline_ms,
            next_retry_at=now_ms,
            auto_confirm=auto_confirm,
            idem_key=tx_idem,
            context=json.dumps(context or {}, ensure_ascii=False),
        )
        branch_rows: list[TccBranch] = []
        for meta, payload, branch_idem in pending:
            payload_text = json.dumps(payload, ensure_ascii=False)
            b = TccBranch.objects.create(
                global_tx=g,
                branch_meta=meta,
                branch_index=meta.branch_index,
                status=BranchStatus.PENDING_TRY,
                idem_key=branch_idem,
                payload=payload_text,
            )
            branch_rows.append(b)

    ordered = sorted(branch_rows, key=lambda x: x.branch_index)
    _execute_try_sequence(g, ordered)
    g.refresh_from_db()
    return serialize_transaction(g)


def _execute_try_sequence(g: TccGlobalTransaction, ordered: list[TccBranch]) -> None:
    succeeded: list[TccBranch] = []
    for b in ordered:
        b = (
            TccBranch.objects.using("tcc_rw")
            .select_related("branch_meta")
            .get(pk=b.pk)
        )
        st, err = participant_http.call_participant(
            url=b.branch_meta.try_url,
            phase=participant_http.PHASE_TRY,
            global_tx_id=str(g.pk),
            branch_id=str(b.pk),
            idempotency_key=_participant_idem_key(b),
            payload=_branch_payload_dict(b),
        )
        with transaction.atomic(using="tcc_rw"):
            b.refresh_from_db()
            b.last_http_status = st if st else None
            b.last_error = err
            if participant_http.is_success_status(st):
                b.status = BranchStatus.TRY_SUCCEEDED
                b.save(using="tcc_rw", update_fields=["last_http_status", "last_error", "status", "ut"])
                succeeded.append(b)
            else:
                b.status = BranchStatus.TRY_FAILED
                b.save(using="tcc_rw", update_fields=["last_http_status", "last_error", "status", "ut"])
                g.refresh_from_db()
                g.status = GlobalTxStatus.CANCELING
                t = get_now_timestamp_ms()
                g.phase_started_at = t
                g.phase_deadline_at = _plus_ms(t, cancel_phase_timeout_delta(len(succeeded)))
                g.next_retry_at = t
                g.save(
                    using="tcc_rw",
                    update_fields=[
                        "status",
                        "phase_started_at",
                        "phase_deadline_at",
                        "next_retry_at",
                        "ut",
                    ],
                )
        if b.status == BranchStatus.TRY_FAILED:
            execute_cancel_reverse(g, succeeded)
            return

    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        if g.status != GlobalTxStatus.TRYING:
            return
        if g.auto_confirm:
            g.status = GlobalTxStatus.CONFIRMING
            t = get_now_timestamp_ms()
            g.phase_started_at = t
            g.phase_deadline_at = _plus_ms(t, confirm_phase_timeout_delta(len(ordered)))
            g.next_retry_at = t
            g.save(
                using="tcc_rw",
                update_fields=[
                    "status",
                    "phase_started_at",
                    "phase_deadline_at",
                    "next_retry_at",
                    "ut",
                ],
            )
        else:
            _enter_await_confirm(g)
            return

    g.refresh_from_db()
    if g.status == GlobalTxStatus.CONFIRMING:
        _execute_confirm_reverse(g, ordered)


def _enter_await_confirm(g: TccGlobalTransaction) -> None:
    t = get_now_timestamp_ms()
    g.status = GlobalTxStatus.AWAIT_CONFIRM
    g.phase_started_at = t
    g.await_confirm_deadline_at = _plus_ms(t, _await_confirm_delta())
    g.phase_deadline_at = None
    g.next_retry_at = t
    g.save(
        using="tcc_rw",
        update_fields=[
            "status",
            "phase_started_at",
            "await_confirm_deadline_at",
            "phase_deadline_at",
            "next_retry_at",
            "ut",
        ],
    )


def _execute_confirm_reverse(g: TccGlobalTransaction, ordered: list[TccBranch]) -> None:
    for b in reversed(ordered):
        b = (
            TccBranch.objects.using("tcc_rw")
            .select_related("branch_meta")
            .get(pk=b.pk)
        )
        if not _invoke_participant_phase_or_mark_manual(
            g=g,
            b=b,
            url=b.branch_meta.confirm_url,
            phase=participant_http.PHASE_CONFIRM,
            status_on_success=BranchStatus.CONFIRM_SUCCEEDED,
            status_on_failure=BranchStatus.CONFIRM_FAILED,
            manual_reason="confirm_failed",
        ):
            return

    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        g.status = GlobalTxStatus.COMMITTED
        g.phase_deadline_at = None
        g.next_retry_at = get_now_timestamp_ms()
        g.save(using="tcc_rw", update_fields=["status", "phase_deadline_at", "next_retry_at", "ut"])


def execute_cancel_reverse(g: TccGlobalTransaction, succeeded: list[TccBranch]) -> None:
    for b in reversed(succeeded):
        b = (
            TccBranch.objects.using("tcc_rw")
            .select_related("branch_meta")
            .get(pk=b.pk)
        )
        if not _invoke_participant_phase_or_mark_manual(
            g=g,
            b=b,
            url=b.branch_meta.cancel_url,
            phase=participant_http.PHASE_CANCEL,
            status_on_success=BranchStatus.CANCEL_SUCCEEDED,
            status_on_failure=BranchStatus.CANCEL_FAILED,
            manual_reason="cancel_failed",
        ):
            return

    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        g.status = GlobalTxStatus.ROLLED_BACK
        g.phase_deadline_at = None
        g.next_retry_at = get_now_timestamp_ms()
        g.save(using="tcc_rw", update_fields=["status", "phase_deadline_at", "next_retry_at", "ut"])


def execute_confirm_reverse_partial(g: TccGlobalTransaction, ordered: list[TccBranch]) -> None:
    for b in reversed(ordered):
        b = (
            TccBranch.objects.using("tcc_rw")
            .select_related("branch_meta")
            .get(pk=b.pk)
        )
        b.refresh_from_db()
        if b.status == BranchStatus.CONFIRM_SUCCEEDED:
            continue
        if not _invoke_participant_phase_or_mark_manual(
            g=g,
            b=b,
            url=b.branch_meta.confirm_url,
            phase=participant_http.PHASE_CONFIRM,
            status_on_success=BranchStatus.CONFIRM_SUCCEEDED,
            status_on_failure=BranchStatus.CONFIRM_FAILED,
            manual_reason="confirm_failed",
        ):
            return

    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        g.status = GlobalTxStatus.COMMITTED
        g.phase_deadline_at = None
        g.next_retry_at = get_now_timestamp_ms()
        g.save(using="tcc_rw", update_fields=["status", "phase_deadline_at", "next_retry_at", "ut"])


def execute_cancel_reverse_partial(g: TccGlobalTransaction, succeeded: list[TccBranch]) -> None:
    for b in reversed(succeeded):
        b = (
            TccBranch.objects.using("tcc_rw")
            .select_related("branch_meta")
            .get(pk=b.pk)
        )
        b.refresh_from_db()
        if b.status == BranchStatus.CANCEL_SUCCEEDED:
            continue
        if not _invoke_participant_phase_or_mark_manual(
            g=g,
            b=b,
            url=b.branch_meta.cancel_url,
            phase=participant_http.PHASE_CANCEL,
            status_on_success=BranchStatus.CANCEL_SUCCEEDED,
            status_on_failure=BranchStatus.CANCEL_FAILED,
            manual_reason="cancel_failed",
        ):
            return

    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        g.status = GlobalTxStatus.ROLLED_BACK
        g.phase_deadline_at = None
        g.next_retry_at = get_now_timestamp_ms()
        g.save(using="tcc_rw", update_fields=["status", "phase_deadline_at", "next_retry_at", "ut"])


def mark_manual_simple(g: TccGlobalTransaction, reason: str, snap: dict[str, Any]) -> None:
    g.status = GlobalTxStatus.NEEDS_MANUAL
    g.manual_reason = reason
    g.next_retry_at = get_now_timestamp_ms() + int(timedelta(days=3650).total_seconds() * 1000)
    snap_json = json.dumps(snap, ensure_ascii=False)
    with transaction.atomic(using="tcc_rw"):
        g.save(
            using="tcc_rw",
            update_fields=["status", "manual_reason", "next_retry_at", "ut"],
        )
        TccManualReview.objects.using("tcc_rw").update_or_create(
            global_tx=g,
            defaults={"snapshot": snap_json},
        )


def confirm_transaction(global_tx_id: str) -> dict[str, Any]:
    g = get_transaction_by_global_id(global_tx_id)
    if not g:
        raise ValueError("transaction not found")
    if g.status != GlobalTxStatus.AWAIT_CONFIRM:
        raise ValueError("transaction is not awaiting confirm")

    ordered = list(
        g.branches.select_related("branch_meta").order_by("branch_index")
    )
    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        if g.status != GlobalTxStatus.AWAIT_CONFIRM:
            raise ValueError("transaction is not awaiting confirm")
        g.status = GlobalTxStatus.CONFIRMING
        t = get_now_timestamp_ms()
        g.phase_started_at = t
        g.phase_deadline_at = _plus_ms(t, confirm_phase_timeout_delta(len(ordered)))
        g.await_confirm_deadline_at = None
        g.next_retry_at = t
        g.save(
            using="tcc_rw",
            update_fields=[
                "status",
                "phase_started_at",
                "phase_deadline_at",
                "await_confirm_deadline_at",
                "next_retry_at",
                "ut",
            ],
        )

    _execute_confirm_reverse(g, ordered)
    g.refresh_from_db()
    return serialize_transaction(g)


def cancel_transaction(global_tx_id: str) -> dict[str, Any]:
    g = get_transaction_by_global_id(global_tx_id)
    if not g:
        raise ValueError("transaction not found")
    if g.status in (
        GlobalTxStatus.COMMITTED,
        GlobalTxStatus.ROLLED_BACK,
        GlobalTxStatus.NEEDS_MANUAL,
    ):
        raise ValueError("transaction is already terminal")

    ordered = list(
        g.branches.select_related("branch_meta").order_by("branch_index")
    )
    succeeded = [b for b in ordered if b.status == BranchStatus.TRY_SUCCEEDED]
    with transaction.atomic(using="tcc_rw"):
        g.refresh_from_db()
        if g.status in (
            GlobalTxStatus.COMMITTED,
            GlobalTxStatus.ROLLED_BACK,
            GlobalTxStatus.NEEDS_MANUAL,
        ):
            raise ValueError("transaction is already terminal")
        g.status = GlobalTxStatus.CANCELING
        t = get_now_timestamp_ms()
        g.phase_started_at = t
        g.phase_deadline_at = _plus_ms(t, cancel_phase_timeout_delta(len(succeeded)))
        g.await_confirm_deadline_at = None
        g.next_retry_at = t
        g.save(
            using="tcc_rw",
            update_fields=[
                "status",
                "phase_started_at",
                "phase_deadline_at",
                "await_confirm_deadline_at",
                "next_retry_at",
                "ut",
            ],
        )

    execute_cancel_reverse(g, succeeded)
    g.refresh_from_db()
    return serialize_transaction(g)
