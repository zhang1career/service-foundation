from __future__ import annotations

import random

from django.conf import settings

from app_verify.enums import RegStatusEnum, VerifyLevelEnum, VerifyLogActionEnum
from app_verify.repos import (
    create_verify_code,
    create_verify_log,
    get_reg_by_access_key,
    get_reg_by_id,
    get_verify_code_by_id,
    mark_verify_code_used,
)
from common.utils.date_util import get_now_timestamp_ms


class VerifyService:
    @staticmethod
    def _as_int(value, field_name: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be int")

    @staticmethod
    def _log_check(
            *,
            reg_id: int,
            ref_id: int,
            code_id: int | None,
            level: int,
            ok: int,
            message: str = "",
    ) -> None:
        create_verify_log(
            reg_id=reg_id,
            ref_id=ref_id,
            code_id=code_id,
            level=level,
            action=int(VerifyLogActionEnum.CODE_CHECK),
            ok=ok,
            message=message,
        )

    @staticmethod
    def _log_request(
            *,
            reg_id: int,
            ref_id: int,
            code_id: int | None,
            level: int,
            ok: int,
            message: str = "",
    ) -> None:
        create_verify_log(
            reg_id=reg_id,
            ref_id=ref_id,
            code_id=code_id,
            level=level,
            action=int(VerifyLogActionEnum.CODE_REQUEST),
            ok=ok,
            message=message,
        )

    @staticmethod
    def _create_code_for_reg(reg, level: int, ref_id: int) -> dict:
        code = f"{random.randint(0, 999999):06d}"
        expires_at = get_now_timestamp_ms() + int(settings.VERIFY_CODE_TTL_SECONDS) * 1000
        code_obj = create_verify_code(
            level=level,
            reg_id=reg.id,
            ref_id=ref_id,
            code=code,
            expires_at=expires_at,
        )
        VerifyService._log_request(
            reg_id=int(reg.id),
            ref_id=ref_id,
            code_id=int(code_obj.id),
            level=level,
            ok=1,
            message="",
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
    def request_code(level: int, access_key: str, ref_id: int) -> dict:
        access_key = (access_key or "").strip()
        if level not in VerifyLevelEnum.values():
            VerifyService._log_request(
                reg_id=0,
                ref_id=ref_id,
                code_id=None,
                level=level if isinstance(level, int) else 0,
                ok=0,
                message="invalid level",
            )
            raise ValueError(f"level must be one of {VerifyLevelEnum.values()}")
        if not access_key:
            VerifyService._log_request(
                reg_id=0, ref_id=ref_id, code_id=None, level=level, ok=0, message="access_key is required"
            )
            raise ValueError("access_key is required")
        reg = get_reg_by_access_key(access_key)
        if not reg or int(reg.status) != RegStatusEnum.ENABLED:
            VerifyService._log_request(
                reg_id=int(reg.id) if reg else 0,
                ref_id=ref_id,
                code_id=None,
                level=level,
                ok=0,
                message="invalid access_key",
            )
            raise ValueError("invalid access_key")
        return VerifyService._create_code_for_reg(reg, level, ref_id)

    @staticmethod
    def issue_code_for_reg_id(reg_id: int, level: int, ref_id: int) -> dict:
        """控制台按调用方主键签发校验码（须为启用状态）；与 request_code 共用落库与 verify_log。"""
        if level not in VerifyLevelEnum.values():
            raise ValueError(f"level must be one of {VerifyLevelEnum.values()}")
        reg = get_reg_by_id(int(reg_id))
        if reg is None or int(reg.status) != RegStatusEnum.ENABLED:
            raise ValueError("invalid or disabled reg")
        return VerifyService._create_code_for_reg(reg, level, int(ref_id))

    @staticmethod
    def code_row_awaits_verification(row) -> bool:
        """未核销且未过期（与校验接口可接受条件一致，不含 reg / 明文比对）。"""
        if row is None:
            return False
        if int(getattr(row, "used_at", 0) or 0) != 0:
            return False
        return int(getattr(row, "expires_at", 0) or 0) > get_now_timestamp_ms()

    @staticmethod
    def verify_code(code_id: int, code: str, access_key: str) -> dict:
        code = (code or "").strip()
        access_key = (access_key or "").strip()
        try:
            cid = int(code_id)
        except (TypeError, ValueError):
            cid = None

        if not code:
            VerifyService._log_check(
                reg_id=0, ref_id=0, code_id=cid, level=0, ok=0, message="code is required"
            )
            raise ValueError("code is required")
        reg = get_reg_by_access_key(access_key)
        if not reg or int(reg.status) != RegStatusEnum.ENABLED:
            VerifyService._log_check(
                reg_id=int(reg.id) if reg else 0,
                ref_id=0,
                code_id=cid,
                level=0,
                ok=0,
                message="invalid access_key",
            )
            raise ValueError("invalid access_key")

        if cid is None:
            VerifyService._log_check(
                reg_id=int(reg.id), ref_id=0, code_id=None, level=0, ok=0, message="invalid code_id"
            )
            raise ValueError("invalid or expired verify code")

        stale = get_verify_code_by_id(cid)
        if stale is None:
            VerifyService._log_check(
                reg_id=int(reg.id), ref_id=0, code_id=cid, level=0, ok=0, message="verify code not found"
            )
            raise ValueError("invalid or expired verify code")

        lv = int(stale.level)
        if int(stale.reg_id) != int(reg.id):
            VerifyService._log_check(
                reg_id=int(reg.id),
                ref_id=int(stale.ref_id),
                code_id=cid,
                level=lv,
                ok=0,
                message="verify code reg mismatch",
            )
            raise ValueError("invalid or expired verify code")

        if not VerifyService.code_row_awaits_verification(stale):
            reason = "already used" if int(stale.used_at or 0) != 0 else "expired"
            VerifyService._log_check(
                reg_id=int(reg.id),
                ref_id=int(stale.ref_id),
                code_id=cid,
                level=lv,
                ok=0,
                message=reason,
            )
            raise ValueError("invalid or expired verify code")

        if stale.code != code:
            VerifyService._log_check(
                reg_id=int(reg.id),
                ref_id=int(stale.ref_id),
                code_id=cid,
                level=lv,
                ok=0,
                message="wrong verify code",
            )
            raise ValueError("invalid or expired verify code")

        mark_verify_code_used(stale.id)
        VerifyService._log_check(
            reg_id=int(reg.id),
            ref_id=int(stale.ref_id),
            code_id=cid,
            level=lv,
            ok=1,
            message="",
        )
        return {
            "verified": True,
            "reg_id": reg.id,
            "ref_id": stale.ref_id,
            "code_id": stale.id,
            "level": lv,
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
            access_key=(payload.get("access_key") or "").strip(),
        )
