from common.exceptions.base_exception import CheckedException


class NoDataException(CheckedException):
    def __init__(self, message: str):
        super(NoDataException, self).__init__(message)
