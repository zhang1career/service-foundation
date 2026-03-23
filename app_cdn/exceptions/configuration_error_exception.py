"""Configuration error exception"""

from app_cdn.exceptions.cdn_exception import CdnException


class ConfigurationErrorException(CdnException):
    """Configuration error exception"""

    def __init__(self, message: str = "Configuration error"):
        self.message = message
        super().__init__(self.message)
