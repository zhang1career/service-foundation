from app_snowflake.exceptions.snowflake_exception import SnowflakeException


class ConfigurationErrorException(SnowflakeException):
    """Configuration error exception"""

    def __init__(self, message="Configuration error"):
        self.message = message
        super().__init__(self.message)
