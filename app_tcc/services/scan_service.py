from __future__ import annotations

import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from app_tcc.enums import BranchStatus, GlobalTxStatus
from app_tcc.models import TccGlobalTransaction
from app_tcc.services import coordinator
from common.utils.date_util import get_now_timestamp_ms
from common.utils.django_util import select_for_update_skip_locked

logger = logging.getLogger(__name__)

# AWAIT_CONFIRM polling backoff (scanner policy; not env defaults).
_AWAIT_CONFIRM_BACKOFF_CAP_SEC = 300
_AWAIT_CONFIRM_BACKOFF_BASE_SEC = 5
_AWAIT_CONFIRM_BACKOFF_STEP_SEC = 10


def _max_retries() -> int:
    return int(settings.TCC_MAX_AUTO_RETRIES)


def _backoff_seconds(retry_count: int) -> int:
    return min(
        _AWAIT_CONFIRM_BACKOFF_CAP_SEC,
        _AWAIT_CONFIRM_BACKOFF_BASE_SEC + retry_count * _AWAIT_CONFIRM_BACKOFF_STEP_SEC,
    )


def _set_next_retry_capped_by_phase_deadline(g: TccGlobalTransaction, now_ms: int) -> None:
    fallback_ms = int(settings.TCC_SCAN_PHASE_DEADLINE_FALLBACK_MS)
    cap_ms = int(settings.TCC_SCAN_NEXT_RETRY_CAP_MS)
    deadline_ms = (
        g.phase_deadline_at if g.phase_deadline_at is not None else now_ms + fallback_ms
    )
    g.next_retry_at = min(deadline_ms, now_ms + cap_ms)
    g.save(using="tcc_rw", update_fields=["next_retry_at", "ut"])


def claim_batch(*, limit: int = 20) -> list[TccGlobalTransaction]:
    """Select rows to process with row lock (``SKIP LOCKED`` when supported)."""
    now_ms = get_now_timestamp_ms()
    active = Q(
        status__in=[
            GlobalTxStatus.TRYING,
            GlobalTxStatus.AWAIT_CONFIRM,
            GlobalTxStatus.CONFIRMING,
            GlobalTxStatus.CANCELING,
        ]
    )
    due_retry = Q(next_retry_at__lte=now_ms)
    due_await = Q(status=GlobalTxStatus.AWAIT_CONFIRM, await_confirm_deadline_at__lte=now_ms)
    due_phase = Q(phase_deadline_at__lte=now_ms) & Q(
        status__in=[GlobalTxStatus.CONFIRMING, GlobalTxStatus.CANCELING]
    )
    with transaction.atomic(using="tcc_rw"):
        qs = (
            select_for_update_skip_locked(TccGlobalTransaction.objects.using("tcc_rw"))
            .filter(active & (due_retry | due_await | due_phase))
            .order_by("next_retry_at")[:limit]
        )
        return list(qs)


def process_one(g: TccGlobalTransaction) -> None:
    now_ms = get_now_timestamp_ms()
    g.refresh_from_db()

    if g.status in (
            GlobalTxStatus.COMMITTED,
            GlobalTxStatus.ROLLED_BACK,
            GlobalTxStatus.NEEDS_MANUAL,
            GlobalTxStatus.INIT,
    ):
        return

    if g.status == GlobalTxStatus.TRYING:
        _bump_retry_or_manual(g, now_ms, "trying_stuck")
        return

    if g.status == GlobalTxStatus.AWAIT_CONFIRM:
        if g.await_confirm_deadline_at is not None and g.await_confirm_deadline_at <= now_ms:
            ordered = list(
                g.branches.select_related("branch_meta").order_by("branch_index")
            )
            succeeded = [b for b in ordered if b.status == BranchStatus.TRY_SUCCEEDED]
            with transaction.atomic(using="tcc_rw"):
                g.refresh_from_db()
                if g.status != GlobalTxStatus.AWAIT_CONFIRM:
                    return
                g.status = GlobalTxStatus.CANCELING
                g.phase_started_at = now_ms
                g.phase_deadline_at = now_ms + int(
                    coordinator.cancel_phase_timeout_delta(len(succeeded)).total_seconds() * 1000
                )
                g.await_confirm_deadline_at = None
                g.next_retry_at = now_ms
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
            coordinator.execute_cancel_reverse(g, succeeded)
        else:
            g.next_retry_at = now_ms + _backoff_seconds(g.retry_count) * 1000
            g.save(using="tcc_rw", update_fields=["next_retry_at", "ut"])
        return

    if g.status == GlobalTxStatus.CONFIRMING:
        if g.phase_deadline_at is not None and g.phase_deadline_at <= now_ms:
            if g.retry_count >= _max_retries():
                coordinator.mark_manual_simple(
                    g, "confirm_phase_timeout", {"at": str(now_ms)}
                )
                return
            ordered = list(
                g.branches.select_related("branch_meta").order_by("branch_index")
            )
            with transaction.atomic(using="tcc_rw"):
                g.refresh_from_db()
                if g.status != GlobalTxStatus.CONFIRMING:
                    return
                g.retry_count += 1
                g.phase_deadline_at = now_ms + int(
                    coordinator.confirm_phase_timeout_delta(len(ordered)).total_seconds() * 1000
                )
                g.next_retry_at = now_ms
                g.save(
                    using="tcc_rw",
                    update_fields=["retry_count", "phase_deadline_at", "next_retry_at", "ut"],
                )
            coordinator.execute_confirm_reverse_partial(g, ordered)
            return
        _set_next_retry_capped_by_phase_deadline(g, now_ms)
        return

    if g.status == GlobalTxStatus.CANCELING:
        if g.phase_deadline_at is not None and g.phase_deadline_at <= now_ms:
            if g.retry_count >= _max_retries():
                coordinator.mark_manual_simple(
                    g, "cancel_phase_timeout", {"at": str(now_ms)}
                )
                return
            ordered = list(
                g.branches.select_related("branch_meta").order_by("branch_index")
            )
            succeeded = [b for b in ordered if b.status == BranchStatus.TRY_SUCCEEDED]
            with transaction.atomic(using="tcc_rw"):
                g.refresh_from_db()
                if g.status != GlobalTxStatus.CANCELING:
                    return
                g.retry_count += 1
                g.phase_deadline_at = now_ms + int(
                    coordinator.cancel_phase_timeout_delta(len(succeeded)).total_seconds() * 1000
                )
                g.next_retry_at = now_ms
                g.save(
                    using="tcc_rw",
                    update_fields=["retry_count", "phase_deadline_at", "next_retry_at", "ut"],
                )
            coordinator.execute_cancel_reverse_partial(g, succeeded)
            return
        _set_next_retry_capped_by_phase_deadline(g, now_ms)
        return


def _bump_retry_or_manual(g: TccGlobalTransaction, now_ms: int, reason: str) -> None:
    if g.retry_count >= _max_retries():
        coordinator.mark_manual_simple(g, reason, {"at": str(now_ms)})
        return
    g.retry_count += 1
    g.next_retry_at = now_ms + _backoff_seconds(g.retry_count) * 1000
    g.save(using="tcc_rw", update_fields=["retry_count", "next_retry_at", "ut"])
