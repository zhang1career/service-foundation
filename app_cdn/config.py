"""
CDN application configuration

This module provides utilities for loading and accessing environment variables
for the CDN application. It supports layered environment variable loading
(.env, .env.test, .env.prod) and provides convenient accessors for CDN-specific
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
    return Path(__file__).resolve().parent.parent.parent


def get_env():
    """
    Load and return environment variables with layered support.

    Returns:
        environ.Env instance with loaded environment variables
    """
    base_dir = get_base_dir()
    return load_env(base_dir)


def get_app_config() -> Dict:
    """
    Get CDN configuration from environment variables.

    Returns:
        Dictionary containing CDN configuration values

    Raises:
        ConfigurationErrorException: If configuration values are invalid
    """
    from app_cdn.exceptions.configuration_error_exception import ConfigurationErrorException

    env = get_env()

    try:
        # OSS bucket for CDN cache (requires APP_OSS_ENABLED)
        cdn_cache_bucket = env("CDN_CACHE_BUCKET", default="cdn-cache")

        return {
            "cdn_cache_bucket": cdn_cache_bucket.strip() or "cdn-cache",
        }
    except Exception as e:
        raise ConfigurationErrorException(
            f"Failed to load CDN configuration: {str(e)}"
        ) from e
