from __future__ import annotations

from common.consts import response_const as rc
from common.exceptions.base_exception import CheckedException


class ObjectStorageError(CheckedException):
    def __init__(
        self,
        detail: str,
        *,
        message: str | None = None,
        http_status: int | None = None,
    ):
        super().__init__(
            detail,
            ret_code=rc.RET_OBJECT_STORAGE_ERROR,
            message=message,
            http_status=http_status,
        )
