from common.exceptions.base_exception import CheckedException


class AbortException(CheckedException):
    """
    Abort, but is not error
    """
    pass
