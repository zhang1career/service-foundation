from __future__ import annotations

import atexit
import logging
import threading
from typing import Dict

import httpx
from django.conf import settings

from common.services.http.pools import HttpClientPool, pool_id

logger = logging.getLogger(__name__)

_CLIENTS: Dict[str, httpx.Client] = {}
_LOCK = threading.Lock()


def get_http_client(
        pool_name: HttpClientPool | str | None = None,
        timeout_sec: float | None = None,
) -> httpx.Client:
    pool_key = pool_id(pool_name)

    with _LOCK:
        client = _CLIENTS.get(pool_key)
        if client is None:
            # Client default timeout from settings only; per-request timeouts pass through
            # request_sync(..., timeout_sec=...) without mutating this shared instance.
            client = httpx.Client(
                limits=_resolve_limits(pool_key),
                timeout=_resolve_timeout(timeout_sec),
                follow_redirects=False,
            )
            _CLIENTS[pool_key] = client
            logger.info("[httpx] initialized pool=%s", pool_key)
            return client

    return client


def _resolve_limits(pool_key: str) -> httpx.Limits:
    default_max_connections = int(getattr(settings, "HTTPX_DEFAULT_MAX_CONNECTIONS", 100))
    default_max_keepalive = int(getattr(settings, "HTTPX_DEFAULT_MAX_KEEPALIVE", 20))
    pool_limits = getattr(settings, "HTTPX_POOL_MAX_CONNECTIONS", None) or {}
    max_connections = int(pool_limits.get(pool_key, default_max_connections))

    return httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=default_max_keepalive,
        keepalive_expiry=float(getattr(settings, "HTTPX_DEFAULT_KEEPALIVE_EXPIRY", 30.0)),
    )


def _resolve_timeout(timeout_sec: float | None) -> httpx.Timeout:
    timeout_value = float(timeout_sec or getattr(settings, "HTTPX_DEFAULT_TIMEOUT", 30.0))
    return httpx.Timeout(timeout_value)


def close_all_http_clients() -> None:
    with _LOCK:
        for pool_name, client in list(_CLIENTS.items()):
            try:
                client.close()
                logger.info("[httpx] closed pool=%s", pool_name)
            except Exception:
                logger.exception("[httpx] failed closing pool=%s", pool_name)
        _CLIENTS.clear()


atexit.register(close_all_http_clients)
