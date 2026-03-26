import time
from typing import Optional

from app_verify.models import VerifyCode


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_verify_code(level: int, reg_id: int, ref_id: int, code: str, expires_at: int) -> VerifyCode:
    return VerifyCode.objects.using("verify_rw").create(
        level=level,
        reg_id=reg_id,
        ref_id=ref_id,
        code=code,
        expires_at=expires_at,
        used_at=0,
        ct=_now_ms(),
    )


def get_valid_code_by_id(code_id: int, level: int, reg_id: int) -> Optional[VerifyCode]:
    now_ms = _now_ms()
    return (
        VerifyCode.objects.using("verify_rw")
        .filter(id=code_id, level=level, reg_id=reg_id, used_at=0, expires_at__gt=now_ms)
        .first()
    )


def mark_verify_code_used(code_id: int) -> bool:
    code_obj = VerifyCode.objects.using("verify_rw").filter(id=code_id).first()
    if not code_obj:
        return False
    code_obj.used_at = _now_ms()
    code_obj.save(using="verify_rw", update_fields=["used_at"])
    return True
