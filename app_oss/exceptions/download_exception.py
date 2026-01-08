from app_oss.exceptions.oss_exception import OSSException


class DownloadException(OSSException):
    """Download exception"""

    def __init__(self, message="Download failed"):
        self.message = message
        super().__init__(self.message)

