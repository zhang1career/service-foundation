"""
Configuration error exception for mail server
"""
from common.exceptions.base_exception import CheckedException


class ConfigurationErrorException(CheckedException):
    def __init__(self, message: str):
        super(ConfigurationErrorException, self).__init__(message)
