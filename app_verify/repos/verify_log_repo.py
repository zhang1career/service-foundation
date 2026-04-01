from __future__ import annotations

from app_verify.constants import VERIFY_BULK_DELETE_MAX
from app_verify.models import VerifyLog
from app_verify.repos.repo_bulk import unique_positive_int_ids
from common.utils.date_util import get_now_timestamp_ms
from common.utils.page_util import slice_window_for_page


def create_verify_log(
        *,
        reg_id: int,
        ref_id: int,
        code_id: int | None,
        level: int,
        action: int,
        ok: int,
        message: str = "",
) -> VerifyLog:
    msg = (message or "").strip()
    if len(msg) > 512:
        msg = msg[:512]
    cid = int(code_id) if code_id is not None and int(code_id) > 0 else None
    return VerifyLog.objects.using("verify_rw").create(
        reg_id=max(0, int(reg_id)),
        ref_id=int(ref_id),
        code_id=cid,
        level=int(level),
        action=int(action),
        ok=1 if int(ok) else 0,
        message=msg,
        ct=get_now_timestamp_ms(),
    )


def list_verify_logs_page(page: int, page_size: int) -> tuple[list[VerifyLog], int, int]:
    ps = page_size if page_size >= 1 else 1
    qs = VerifyLog.objects.using("verify_rw").order_by("-ct", "-id")
    total = qs.count()
    offset, resolved, _ = slice_window_for_page(total, page, ps)
    rows = list(qs[offset: offset + ps])
    return rows, total, resolved


def get_verify_log_by_id(log_id: int) -> VerifyLog | None:
    try:
        return VerifyLog.objects.using("verify_rw").get(pk=log_id)
    except VerifyLog.DoesNotExist:
        return None


def delete_verify_log_by_id(log_id: int) -> int:
    deleted, _ = VerifyLog.objects.using("verify_rw").filter(pk=log_id).delete()
    return int(deleted)


def delete_verify_logs_by_ids(log_ids: list[int]) -> int:
    uniq = unique_positive_int_ids(log_ids, VERIFY_BULK_DELETE_MAX)
    if not uniq:
        return 0
    total, _ = VerifyLog.objects.using("verify_rw").filter(pk__in=uniq).delete()
    return int(total)
