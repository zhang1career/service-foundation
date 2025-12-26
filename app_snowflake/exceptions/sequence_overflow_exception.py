from app_snowflake.exceptions.configuration_error_exception import SnowflakeException


class SequenceOverflowException(SnowflakeException):
    """Sequence overflow exception"""

    def __init__(self, message="Sequence overflow"):
        self.message = message
        super().__init__(self.message)
