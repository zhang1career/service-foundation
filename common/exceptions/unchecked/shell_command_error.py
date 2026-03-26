from common.consts import response_const as rc
from common.exceptions.base_exception import UncheckedException


class ShellCommandError(UncheckedException):
    def __init__(self, detail: str, *, ret_code: int = rc.RET_FILE_IO_ERROR):
        super().__init__(detail, ret_code=ret_code)
