from __future__ import annotations

from app_tcc.enums import GlobalTxStatus
from app_tcc.models import TccBranch, TccGlobalTransaction, TccManualReview

_PAGE = 50


def list_transactions(
    *,
    status: int | None = None,
    page: int = 1,
    page_size: int = _PAGE,
) -> tuple[int, list[TccGlobalTransaction]]:
    qs = TccGlobalTransaction.objects.using("tcc_rw").order_by("-id")
    if status is not None:
        qs = qs.filter(status=status)
    total = qs.count()
    page = max(1, page)
    offset = (page - 1) * page_size
    rows = list(qs[offset : offset + page_size])
    return total, rows


def get_transaction(tx_id: int) -> TccGlobalTransaction | None:
    return TccGlobalTransaction.objects.using("tcc_rw").filter(pk=tx_id).first()


def list_tx_branches(tx_id: int) -> list[TccBranch]:
    return list(
        TccBranch.objects.using("tcc_rw")
        .filter(global_tx_id=tx_id)
        .select_related("branch_meta")
        .order_by("branch_index")
    )


def get_manual_review(tx_id: int) -> TccManualReview | None:
    return (
        TccManualReview.objects.using("tcc_rw")
        .filter(global_tx_id=tx_id)
        .first()
    )


def list_needs_manual(*, page: int = 1, page_size: int = _PAGE) -> tuple[int, list[TccGlobalTransaction]]:
    qs = (
        TccGlobalTransaction.objects.using("tcc_rw")
        .filter(status=GlobalTxStatus.NEEDS_MANUAL)
        .order_by("-id")
    )
    total = qs.count()
    page = max(1, page)
    offset = (page - 1) * page_size
    rows = list(qs[offset : offset + page_size])
    return total, rows


def manual_reviews_by_tx_ids(tx_ids: list[int]) -> dict[int, TccManualReview]:
    if not tx_ids:
        return {}
    rows = (
        TccManualReview.objects.using("tcc_rw")
        .filter(global_tx_id__in=tx_ids)
        .order_by("id")
    )
    return {m.global_tx_id: m for m in rows}
