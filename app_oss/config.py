"""
OSS application configuration

This module provides utilities for loading and accessing environment variables
for the OSS application. It supports layered environment variable loading
(.env, .env.test, .env.prod) and provides convenient accessors for OSS-specific
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
    # app_oss/config.py -> app_oss -> service_foundation -> project root
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
    Get OSS configuration from environment variables.
    
    Returns:
        Dictionary containing OSS configuration values
        
    Raises:
        ConfigurationErrorException: If configuration values are invalid
    """
    from app_oss.exceptions.configuration_error_exception import ConfigurationErrorException
    
    env = get_env()
    
    try:
        # Local storage configuration
        storage_path = env("OSS_STORAGE_PATH", default=None)
        bucket_name = env("OSS_BUCKET_NAME", default=None)
        
        # Validate storage path
        if not storage_path:
            raise ConfigurationErrorException(
                "OSS_STORAGE_PATH is required"
            )
        # Convert to Path and ensure it exists
        from pathlib import Path
        storage_path = Path(storage_path).resolve()
        storage_path.mkdir(parents=True, exist_ok=True)
        
        return {
            "storage_path": str(storage_path),
            "bucket_name": bucket_name,
        }
    except Exception as e:
        raise ConfigurationErrorException(
            f"Failed to load OSS configuration: {str(e)}"
        ) from e

