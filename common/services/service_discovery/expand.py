"""
Resolve Fusio-style ``://{{service_key}}`` URLs via the service registry in Redis
(Paganini ``RedisServiceUriResolver`` / mall-agg compatible).

Each call performs a fresh Redis GET and instance pick (no process-local cache).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast, Optional

from django.conf import settings

if TYPE_CHECKING:
    from redis.client import Redis

from common.services.service_discovery.service_uri_list import parse_comma_separated, pick_instance
from common.services.service_discovery.url_specifier import specify_service_host
from common.utils.redis_url_util import redis_location_with_db
from common.utils.service_url_template import ServiceUrlResolutionError

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


def reset_service_discovery_redis_client_for_tests() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            close = getattr(_redis_client, "close", None)
            if callable(close):
                close()
        except Exception:
            logger.debug("service_discovery redis close failed", exc_info=True)
    _redis_client = None


def _service_discovery_redis_url() -> str:
    explicit = (getattr(settings, "SERVICE_DISCOVERY_REDIS_URL", "") or "").strip()
    if explicit:
        return explicit
    base = getattr(settings, "REDIS_URL", "") or "redis://127.0.0.1:6379"
    db = int(getattr(settings, "SERVICE_DISCOVERY_REDIS_DB", 0))
    return redis_location_with_db(base, db)


def _get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        import redis

        _redis_client = redis.Redis.from_url(
            _service_discovery_redis_url(),
            decode_responses=True,
        )
    return _redis_client


def _redis_resolve_host(service_key: str, index: int | None) -> str:
    prefix = getattr(settings, "SERVICE_DISCOVERY_KEY_PREFIX", "")
    rkey = prefix + service_key
    try:
        client = _get_redis_client()
        raw = cast(Optional[str], client.get(rkey))
    except Exception as e:
        raise ServiceUrlResolutionError(
            f"Redis service discovery failed for {{{{{service_key}}}}}: {e}"
        ) from e
    if raw is None or raw == "":
        raise ServiceUrlResolutionError(
            f"No data found for service: {service_key} (redis key {rkey!r})"
        )
    hosts = parse_comma_separated(raw)
    if not hosts:
        raise ServiceUrlResolutionError(f"Empty instance list for service: {service_key}")
    try:
        return pick_instance(hosts, index)
    except ValueError as e:
        raise ServiceUrlResolutionError(str(e)) from e


def expand_service_discovery_url(url: str, index: int | None = None) -> str:
    if not url:
        return ""
    if "://{{" not in url:
        return url.rstrip("/")
    return specify_service_host(url, _redis_resolve_host, index).rstrip("/")
