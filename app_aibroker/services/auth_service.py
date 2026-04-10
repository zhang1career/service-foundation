from typing import TYPE_CHECKING, Optional, Tuple

from common.enums.service_reg_status_enum import ServiceRegStatus

if TYPE_CHECKING:
    from app_aibroker.models.reg import Reg


def _get_reg_by_access_key(access_key: str):
    from app_aibroker.repos.reg_repo import get_reg_by_access_key

    return get_reg_by_access_key(access_key)


def resolve_reg(payload: dict, headers=None) -> Tuple[Optional["Reg"], str]:
    access_key = (payload.get("access_key") or "").strip()
    if not access_key and headers is not None:
        if hasattr(headers, "get"):
            access_key = (headers.get("X-Access-Key") or "").strip()
    if not access_key:
        return None, "access_key is required"
    reg = _get_reg_by_access_key(access_key)
    if not reg or reg.status != ServiceRegStatus.ENABLED:
        return None, "invalid access_key"
    return reg, ""
