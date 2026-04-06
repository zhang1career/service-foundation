"""Helpers for Redis URLs used by Django cache and similar clients."""

import re

_REDIS_TRAILING_DB = re.compile(r"/\d+$")


def redis_location_with_db(base_url: str, db: int) -> str:
    """
    Append a logical database index to a Redis base URL.

    Strips a trailing /N segment if present so callers are not doubled up with
    USER_CACHE_REDIS_DB when migrating from REDIS_CACHE_URL=.../1 style configs.
    """
    base = base_url.rstrip("/")
    base = _REDIS_TRAILING_DB.sub("", base)
    return f"{base}/{db}"
