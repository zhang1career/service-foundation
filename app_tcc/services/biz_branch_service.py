from __future__ import annotations

from django.db import transaction

from app_tcc.models import TccBizMeta, TccBranchMeta, TccParticipant
from common.enums.service_reg_status_enum import ServiceRegStatus


def list_biz_for_participant(participant_id: int) -> list[TccBizMeta]:
    return list(
        TccBizMeta.objects.using("tcc_rw")
        .filter(participant_id=participant_id)
        .select_related("participant")
        .order_by("id")
    )


def list_all_biz_meta() -> list[TccBizMeta]:
    return list(
        TccBizMeta.objects.using("tcc_rw")
        .select_related("participant")
        .order_by("id")
    )


def get_biz_meta(biz_id: int) -> TccBizMeta | None:
    return (
        TccBizMeta.objects.using("tcc_rw")
        .select_related("participant")
        .filter(pk=biz_id)
        .first()
    )


def _ensure_participant_exists_for_biz(participant_id: int) -> None:
    if not TccParticipant.objects.using("tcc_rw").filter(pk=participant_id).exists():
        raise ValueError("participant not found")


@transaction.atomic(using="tcc_rw")
def create_biz_meta(
    participant_id: int,
    *,
    name: str = "",
) -> TccBizMeta:
    _ensure_participant_exists_for_biz(participant_id)
    b = TccBizMeta(
        participant_id=participant_id,
        name=(name or "").strip(),
    )
    b.save(using="tcc_rw")
    return b


@transaction.atomic(using="tcc_rw")
def delete_biz_meta(biz_id: int) -> bool:
    deleted, _ = TccBizMeta.objects.using("tcc_rw").filter(pk=biz_id).delete()
    return deleted > 0


def list_branch_meta_for_biz(biz_id: int) -> list[TccBranchMeta]:
    return list(
        TccBranchMeta.objects.using("tcc_rw")
        .filter(biz_id=biz_id)
        .order_by("branch_index", "id")
    )


@transaction.atomic(using="tcc_rw")
def create_branch_meta(
    biz_id: int,
    *,
    branch_index: int,
    try_url: str,
    confirm_url: str,
    cancel_url: str,
) -> TccBranchMeta:
    if not TccBizMeta.objects.using("tcc_rw").filter(pk=biz_id).exists():
        raise ValueError("biz_meta not found")
    m = TccBranchMeta(
        biz_id=biz_id,
        branch_index=int(branch_index),
        try_url=(try_url or "").strip(),
        confirm_url=(confirm_url or "").strip(),
        cancel_url=(cancel_url or "").strip(),
    )
    m.save(using="tcc_rw")
    return m


@transaction.atomic(using="tcc_rw")
def update_branch_meta(
    pk: int,
    *,
    branch_index: int | None = None,
    try_url: str | None = None,
    confirm_url: str | None = None,
    cancel_url: str | None = None,
) -> TccBranchMeta | None:
    m = TccBranchMeta.objects.using("tcc_rw").filter(pk=pk).first()
    if not m:
        return None
    if branch_index is not None:
        m.branch_index = int(branch_index)
    if try_url is not None:
        m.try_url = try_url.strip()
    if confirm_url is not None:
        m.confirm_url = confirm_url.strip()
    if cancel_url is not None:
        m.cancel_url = cancel_url.strip()
    m.save(using="tcc_rw")
    return m


@transaction.atomic(using="tcc_rw")
def delete_branch_meta(pk: int) -> bool:
    deleted, _ = TccBranchMeta.objects.using("tcc_rw").filter(pk=pk).delete()
    return deleted > 0


@transaction.atomic(using="tcc_rw")
def swap_branch_meta_order(biz_id: int, branch_meta_id: int, direction: str) -> None:
    rows = list(
        TccBranchMeta.objects.using("tcc_rw")
        .filter(biz_id=biz_id)
        .order_by("branch_index", "id")
    )
    if len(rows) < 2:
        return
    idx = next((i for i, r in enumerate(rows) if r.id == branch_meta_id), None)
    if idx is None:
        return
    if direction == "up" and idx == 0:
        return
    if direction == "down" and idx >= len(rows) - 1:
        return
    if direction == "up":
        rows[idx], rows[idx - 1] = rows[idx - 1], rows[idx]
    elif direction == "down":
        rows[idx], rows[idx + 1] = rows[idx + 1], rows[idx]
    else:
        return
    base = max((r.branch_index for r in rows), default=0) + 100000
    for i, r in enumerate(rows):
        r.branch_index = base + i
        r.save(using="tcc_rw", update_fields=["branch_index", "ut"])
    for i, r in enumerate(rows):
        r.branch_index = i
        r.save(using="tcc_rw", update_fields=["branch_index", "ut"])


def load_branch_metas_for_begin(branch_meta_ids: list[int]) -> list[TccBranchMeta]:
    if not branch_meta_ids:
        raise ValueError("branch_meta_ids is required")
    if len(set(branch_meta_ids)) != len(branch_meta_ids):
        raise ValueError("duplicate branch_meta_id")
    metas = list(
        TccBranchMeta.objects.using("tcc_rw")
        .filter(pk__in=branch_meta_ids)
        .select_related("biz", "biz__participant")
    )
    if len(metas) != len(branch_meta_ids):
        raise ValueError("unknown branch_meta_id")
    biz_ids = {m.biz_id for m in metas}
    if len(biz_ids) != 1:
        raise ValueError("branches must belong to the same biz_meta")
    p = metas[0].biz.participant
    if p.status != ServiceRegStatus.ENABLED.value:
        raise ValueError("participant is disabled")
    return sorted(metas, key=lambda m: m.branch_index)
