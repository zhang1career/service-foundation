import random
import time

from app_verify.enums import VerifyLevelEnum
from app_verify.repos import create_verify_code, get_valid_code_by_id, mark_verify_code_used, get_reg_by_access_key


class VerifyService:
    DEFAULT_TTL_MS = 10 * 60 * 1000

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _as_int(value, field_name: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be int")

    @staticmethod
    def request_code(level: int, access_key: str, ref_id: int) -> dict:
        access_key = (access_key or "").strip()
        if level not in VerifyLevelEnum.values():
            raise ValueError(f"level must be one of {VerifyLevelEnum.values()}")
        if not access_key:
            raise ValueError("access_key is required")
        reg = get_reg_by_access_key(access_key)
        if not reg or reg.status != 1:
            raise ValueError("invalid access_key")

        code = f"{random.randint(0, 999999):06d}"
        expires_at = VerifyService._now_ms() + VerifyService.DEFAULT_TTL_MS
        code_obj = create_verify_code(
            level=level,
            reg_id=reg.id,
            ref_id=ref_id,
            code=code,
            expires_at=expires_at,
        )
        return {
            "code_id": code_obj.id,
            "code": code,
            "expires_at": expires_at,
            "reg_id": reg.id,
            "ref_id": ref_id,
            "level": level,
        }

    @staticmethod
    def verify_code(code_id: int, code: str, level: int, access_key: str) -> dict:
        code = (code or "").strip()
        access_key = (access_key or "").strip()
        if level not in VerifyLevelEnum.values():
            raise ValueError(f"level must be one of {VerifyLevelEnum.values()}")
        if not code:
            raise ValueError("code is required")
        reg = get_reg_by_access_key(access_key)
        if not reg or reg.status != 1:
            raise ValueError("invalid access_key")

        verify_code_obj = get_valid_code_by_id(code_id=code_id, level=level, reg_id=reg.id)
        if not verify_code_obj or verify_code_obj.code != code:
            raise ValueError("invalid or expired verify code")
        mark_verify_code_used(verify_code_obj.id)
        return {
            "verified": True,
            "reg_id": reg.id,
            "ref_id": verify_code_obj.ref_id,
            "code_id": verify_code_obj.id,
            "level": level,
        }

    @staticmethod
    def request_code_by_payload(payload: dict) -> dict:
        return VerifyService.request_code(
            level=VerifyService._as_int(payload.get("level"), "level"),
            access_key=(payload.get("access_key") or "").strip(),
            ref_id=VerifyService._as_int(payload.get("ref_id", 0) or 0, "ref_id"),
        )

    @staticmethod
    def verify_code_by_payload(payload: dict) -> dict:
        return VerifyService.verify_code(
            code_id=VerifyService._as_int(payload.get("code_id"), "code_id"),
            code=(payload.get("code") or "").strip(),
            level=VerifyService._as_int(payload.get("level"), "level"),
            access_key=(payload.get("access_key") or "").strip(),
        )
