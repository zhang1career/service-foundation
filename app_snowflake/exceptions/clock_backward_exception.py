from app_snowflake.exceptions.configuration_error_exception import SnowflakeException


class ClockBackwardException(SnowflakeException):
    """Clock backward exception"""

    def __init__(self, message="Clock backward detected"):
        self.message = message
        super().__init__(self.message)
