"""
Mail server application configuration

This module provides utilities for loading and accessing environment variables
for the mail server application. It supports layered environment variable loading
(.env, .env.test, .env.prod) and provides convenient accessors for mail-specific
configuration values.
"""
from pathlib import Path
from typing import Dict

from common.utils.env_util import load_env


def get_base_dir() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root directory
    """
    # Get the project root directory (three levels up from this file)
    # app_mailserver/config.py -> app_mailserver -> service_foundation -> project root
    return Path(__file__).resolve().parent.parent.parent


def get_env():
    """
    Load and return environment variables with layered support.
    
    This function loads environment variables from:
    1. .env (base/default configuration)
    2. .env.test or .env.prod (if ENVIRONMENT is set)
    
    Returns:
        environ.Env instance with loaded environment variables
    """
    base_dir = get_base_dir()
    return load_env(base_dir)


def get_app_config() -> Dict:
    """
    Get mail server configuration from environment variables.
    
    Returns:
        Dictionary containing mail server configuration values
        
    Raises:
        ConfigurationErrorException: If configuration values are invalid
    """
    from common.exceptions.configuration_error_exception import ConfigurationErrorException
    
    env = get_env()
    
    try:
        # SMTP server configuration
        smtp_port = env.int("MAIL_SMTP_PORT", default=25)
        
        # IMAP server configuration
        imap_port = env.int("MAIL_IMAP_PORT", default=143)
        
        # OSS configuration for attachments
        oss_bucket = env("MAIL_OSS_BUCKET", default="mail-attachments")
        oss_endpoint = env("MAIL_OSS_ENDPOINT", default="http://localhost:8000/api/oss")
        
        # Server host configuration
        server_host = env("MAIL_SERVER_HOST", default="0.0.0.0")
        
        return {
            "smtp_port": smtp_port,
            "imap_port": imap_port,
            "oss_bucket": oss_bucket,
            "oss_endpoint": oss_endpoint,
            "server_host": server_host,
        }
    except Exception as e:
        raise ConfigurationErrorException(
            f"Failed to load mail server configuration: {str(e)}"
        ) from e

