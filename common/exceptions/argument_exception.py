from common.exceptions.base_exception import CheckedException


class IllegalArgumentException(CheckedException):
    def __init__(self, message: str):
        super(IllegalArgumentException, self).__init__(message)
