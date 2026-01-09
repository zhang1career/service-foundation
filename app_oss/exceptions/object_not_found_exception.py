from app_oss.exceptions.oss_exception import OSSException


class ObjectNotFoundException(OSSException):
    """Object not found exception"""

    def __init__(self, message="Object not found"):
        self.message = message
        super().__init__(self.message)

