from app_oss.exceptions.oss_exception import OSSException


class ConfigurationErrorException(OSSException):
    """Configuration error exception"""

    def __init__(self, message="Configuration error"):
        self.message = message
        super().__init__(self.message)

