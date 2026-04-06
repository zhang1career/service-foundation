from __future__ import annotations

from app_user.enums import UserDispositionEnum
from common.consts.response_const import RET_ACCOUNT_RESTRICTED

LOGIN_FORBIDDEN_PUBLIC_MESSAGE = "账户已被自动锁定（禁止登录），请联系管理员处理。"


def error_for_user_disposition(user) -> tuple[int, str] | None:
    """If the user has an active disposition, return (errorCode, message) for API responses."""
    if user.ctrl_status == UserDispositionEnum.NONE.value:
        return None
    if user.ctrl_status == UserDispositionEnum.LOGIN_FORBIDDEN.value:
        return RET_ACCOUNT_RESTRICTED, LOGIN_FORBIDDEN_PUBLIC_MESSAGE
    raise ValueError(f"unknown ctrl_status {user.ctrl_status}")
