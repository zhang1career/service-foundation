"""Map Django DB exceptions to API error codes and client-safe messages."""

from django.db import IntegrityError

from common.consts.response_const import RET_DB_DUPLICATE_KEY, RET_RESOURCE_EXISTS


def normalize_optional_contact(value: str | None) -> str | None:
    """Blank or whitespace-only contact values are stored as NULL, not empty string."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def integrity_error_to_client(exc: IntegrityError) -> tuple[int, str]:
    """Translate IntegrityError into (errorCode, message) for API responses."""
    msg_lower = str(exc).lower()
    if "email" in msg_lower:
        return RET_RESOURCE_EXISTS, "email already exists"
    if "phone" in msg_lower:
        return RET_RESOURCE_EXISTS, "phone already exists"
    if "name" in msg_lower or "username" in msg_lower:
        return RET_RESOURCE_EXISTS, "username already exists"
    return RET_DB_DUPLICATE_KEY, "数据冲突"
