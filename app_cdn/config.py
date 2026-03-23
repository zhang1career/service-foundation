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
        # CDN base URL for distribution domain (e.g. http://localhost:8000/api/cdn)
        cdn_base_url = env("CDN_BASE_URL", default="")
        # Default origin URL when creating distribution (e.g. http://localhost:8000/api/oss)
        default_origin_url = env("CDN_DEFAULT_ORIGIN_URL", default="")
        # Default origin ID
        default_origin_id = env("CDN_DEFAULT_ORIGIN_ID", default="default")
        # OSS bucket for CDN cache (requires APP_OSS_ENABLED)
        cdn_cache_bucket = env("CDN_CACHE_BUCKET", default="cdn-cache")
        # When origin is OSS, default bucket for path (e.g. /images/x -> /api/oss/{bucket}/images/x)
        origin_default_bucket = env("CDN_ORIGIN_DEFAULT_BUCKET", default="")

        return {
            "cdn_base_url": cdn_base_url.strip() if cdn_base_url else "",
            "default_origin_url": default_origin_url.strip() if default_origin_url else "",
            "default_origin_id": default_origin_id.strip() or "default",
            "cdn_cache_bucket": cdn_cache_bucket.strip() or "cdn-cache",
            "origin_default_bucket": origin_default_bucket.strip() or "",
        }
    except Exception as e:
        raise ConfigurationErrorException(
            f"Failed to load CDN configuration: {str(e)}"
        ) from e
