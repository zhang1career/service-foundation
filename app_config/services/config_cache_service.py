"""Redis cache for config query results; generation bump per caller (rid)."""

from django.conf import settings
from django.core.cache import caches


def _cache():
    return caches["config"]


def bump_config_cache_generation(rid: int) -> None:
    """Invalidate logical query keys for this caller by incrementing generation."""
    key = f"rid_gen:{rid}"
    c = _cache()
    try:
        c.incr(key)
    except ValueError:
        c.set(key, 1, timeout=None)


def get_rid_generation(rid: int) -> int:
    v = _cache().get(f"rid_gen:{rid}")
    if v is None:
        return 0
    return int(v)


def query_cache_get(rid: int, rid_gen: int, config_key: str, cond_hash: str, scope: str):
    k = f"q:{rid_gen}:{rid}:{config_key}:{cond_hash}:{scope}"
    return _cache().get(k)


def query_cache_set(rid: int, rid_gen: int, config_key: str, cond_hash: str, scope: str, payload: dict) -> None:
    k = f"q:{rid_gen}:{rid}:{config_key}:{cond_hash}:{scope}"
    ttl = int(getattr(settings, "CONFIG_CACHE_TTL_SECONDS", 300) or 300)
    _cache().set(k, payload, timeout=ttl)
