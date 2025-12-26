from common.exceptions.base_exception import CheckedException


class HttpException(CheckedException):
    def __init__(self, message: str):
        super(HttpException, self).__init__(message)
