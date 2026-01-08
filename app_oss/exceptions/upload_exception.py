from app_oss.exceptions.oss_exception import OSSException


class UploadException(OSSException):
    """Upload exception"""

    def __init__(self, message="Upload failed"):
        self.message = message
        super().__init__(self.message)

