from __future__ import annotations

from app_verify.constants import VERIFY_BULK_DELETE_MAX
from app_verify.models import VerifyCode
from app_verify.repos.repo_bulk import unique_positive_int_ids
from common.utils.date_util import get_now_timestamp_ms
from common.utils.page_util import slice_window_for_page


def create_verify_code(level: int, reg_id: int, ref_id: int, code: str, expires_at: int) -> VerifyCode:
    return VerifyCode.objects.using("verify_rw").create(
        level=level,
        reg_id=reg_id,
        ref_id=ref_id,
        code=code,
        expires_at=expires_at,
        used_at=0,
        ct=get_now_timestamp_ms(),
    )


def mark_verify_code_used(code_id: int) -> bool:
    code_obj = VerifyCode.objects.using("verify_rw").filter(id=code_id).first()
    if not code_obj:
        return False
    code_obj.used_at = get_now_timestamp_ms()
    code_obj.save(using="verify_rw", update_fields=["used_at"])
    return True


def get_verify_code_by_id(code_id: int) -> VerifyCode | None:
    try:
        return VerifyCode.objects.using("verify_rw").filter(pk=int(code_id)).first()
    except (TypeError, ValueError):
        return None


def list_verify_codes_page(page: int, page_size: int) -> tuple[list[VerifyCode], int, int]:
    ps = page_size if page_size >= 1 else 1
    qs = VerifyCode.objects.using("verify_rw").order_by("-ct", "-id")
    total = qs.count()
    offset, resolved, _ = slice_window_for_page(total, page, ps)
    rows = list(qs[offset: offset + ps])
    return rows, total, resolved


def delete_verify_code_by_id(code_id: int) -> int:
    deleted, _ = VerifyCode.objects.using("verify_rw").filter(pk=code_id).delete()
    return int(deleted)


def delete_verify_codes_by_ids(code_ids: list[int]) -> int:
    uniq = unique_positive_int_ids(code_ids, VERIFY_BULK_DELETE_MAX)
    if not uniq:
        return 0
    total, _ = VerifyCode.objects.using("verify_rw").filter(pk__in=uniq).delete()
    return int(total)
