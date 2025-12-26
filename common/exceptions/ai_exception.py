from common.exceptions.base_exception import CheckedException


class UnexpectedAnswerException(CheckedException):
    def __init__(self, message: str):
        super(UnexpectedAnswerException, self).__init__(message)
