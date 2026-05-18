"""Registration notice verification (``auth_status != 0``) and resume rate limits."""

from django.conf import settings

from app_user.services.register_resume_throttle import (
    register_resume_ip_count,
    register_resume_user_count,
)
from common.consts.response_const import (
    RET_RATE_LIMITED,
    RET_REGISTRATION_INCOMPLETE,
)
from common.exceptions.base_exception import CheckedException

_PUBLIC_MESSAGE = "请先完成注册渠道验证（邮箱或手机验证码）。"


def assert_registration_notice_verified(user) -> None:
    if int(user.auth_status) == 0:
        raise CheckedException(
            detail="registration notice not verified",
            ret_code=RET_REGISTRATION_INCOMPLETE,
            message=_PUBLIC_MESSAGE,
            http_status=200,
        )


def assert_register_resume_rate_limits(*, client_ip: str, user_id: int) -> None:
    if register_resume_ip_count(client_ip) > int(settings.USER_REGISTER_RESUME_IP_MAX):
        raise CheckedException(
            detail="register resume ip rate limit",
            ret_code=RET_RATE_LIMITED,
            message="尝试次数过多，请稍后再试。",
            http_status=200,
        )
    if register_resume_user_count(user_id) > int(settings.USER_REGISTER_RESUME_USER_MAX):
        raise CheckedException(
            detail="register resume user rate limit",
            ret_code=RET_RATE_LIMITED,
            message="尝试次数过多，请稍后再试。",
            http_status=200,
        )
