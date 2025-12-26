class CheckedException(Exception):
    def __init__(self, message: str):
        super(CheckedException, self).__init__(message)


class UncheckedException(Exception):
    def __init__(self, message: str):
        super(UncheckedException, self).__init__(message)
