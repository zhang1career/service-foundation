"""
Base exception for mail server
"""

from common.consts import response_const as rc
from common.exceptions.base_exception import CheckedException


class MailException(CheckedException):
    """Expected mail pipeline / client errors."""

    def __init__(
        self,
        detail: str,
        *,
        ret_code: int = rc.RET_THIRD_PARTY_ERROR,
        message: str | None = None,
        http_status: int | None = None,
    ):
        super().__init__(
            detail,
            ret_code=ret_code,
            message=message,
            http_status=http_status,
        )
