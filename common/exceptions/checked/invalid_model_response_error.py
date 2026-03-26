from __future__ import annotations

from common.consts import response_const as rc
from common.exceptions.base_exception import CheckedException


class InvalidModelResponseError(CheckedException):
    def __init__(
        self,
        detail: str,
        *,
        message: str | None = None,
        http_status: int | None = None,
    ):
        super().__init__(
            detail,
            ret_code=rc.RET_MODEL_RESPONSE_INVALID,
            message=message,
            http_status=http_status,
        )
