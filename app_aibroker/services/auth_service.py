from typing import Optional, Tuple

from app_aibroker.models import Reg
from app_aibroker.repos import get_reg_by_access_key


def resolve_reg(payload: dict, headers=None) -> Tuple[Optional[Reg], str]:
    access_key = (payload.get("access_key") or "").strip()
    if not access_key and headers is not None:
        if hasattr(headers, "get"):
            access_key = (headers.get("X-Access-Key") or "").strip()
    if not access_key:
        return None, "access_key is required"
    reg = get_reg_by_access_key(access_key)
    if not reg or reg.status != 1:
        return None, "invalid access_key"
    return reg, ""
