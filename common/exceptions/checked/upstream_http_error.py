from __future__ import annotations

from common.consts import response_const as rc
from common.exceptions.base_exception import CheckedException


class UpstreamHttpError(CheckedException):
    """HTTP client helper: non-2xx from a dependency."""

    def __init__(
        self,
        detail: str,
        *,
        ret_code: int = rc.RET_DEPENDENCY_ERROR,
        message: str | None = None,
        http_status: int = 502,
    ):
        super().__init__(
            detail,
            ret_code=ret_code,
            message=message,
            http_status=http_status,
        )
