"""
Snowflake application configuration

This module provides utilities for loading and accessing environment variables
for the Snowflake application. It supports layered environment variable loading
(.env, .env.test, .env.prod) and provides convenient accessors for Snowflake-specific
configuration values.
"""
from pathlib import Path
from typing import Tuple

from common.utils.env_util import load_env


def get_base_dir() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root directory
    """
    # Get the project root directory (three levels up from this file)
    # app_snowflake/config.py -> app_snowflake -> service_foundation -> project root
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


def get_app_config() -> dict:
    """
    Get Snowflake generator configuration from environment variables.
    
    Returns:
        Tuple of (datacenter_id, machine_id, start_timestamp)
        
    Raises:
        ConfigurationErrorException: If configuration values are invalid
    """
    from app_snowflake.exceptions.configuration_error_exception import ConfigurationErrorException
    
    env = get_env()
    
    try:
        datacenter_id = env.int("SNOWFLAKE_DATACENTER_ID", default=0)
        machine_id = env.int("SNOWFLAKE_MACHINE_ID", default=0)
        start_timestamp = env.int("SNOWFLAKE_START_TIMESTAMP", default=1609459200000)
        
        return {
            "datacenter_id": datacenter_id,
            "machine_id": machine_id,
            "start_timestamp": start_timestamp,
        }
    except Exception as e:
        raise ConfigurationErrorException(
            f"Failed to load Snowflake configuration: {str(e)}"
        ) from e

