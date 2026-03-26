import atexit
import logging
import threading
from typing import Dict

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_CLIENTS: Dict[str, httpx.Client] = {}
_LOCK = threading.Lock()


def _resolve_limits(pool_name: str) -> httpx.Limits:
    default_max_connections = int(getattr(settings, "HTTPX_DEFAULT_MAX_CONNECTIONS", 100))
    default_max_keepalive = int(getattr(settings, "HTTPX_DEFAULT_MAX_KEEPALIVE", 20))
    max_connections = default_max_connections

    if pool_name == "avatar_http_pool":
        max_connections = int(getattr(settings, "HTTPX_AVATAR_MAX_CONNECTIONS", 32))
    elif pool_name == "webhook_pool":
        max_connections = int(getattr(settings, "HTTPX_WEBHOOK_MAX_CONNECTIONS", 64))
    elif pool_name == "thirdparty_pool":
        max_connections = int(getattr(settings, "HTTPX_THIRDPARTY_MAX_CONNECTIONS", 64))

    return httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=default_max_keepalive,
        keepalive_expiry=float(getattr(settings, "HTTPX_DEFAULT_KEEPALIVE_EXPIRY", 30.0)),
    )


def _resolve_timeout(timeout_sec: float | None) -> httpx.Timeout:
    timeout_value = float(timeout_sec or getattr(settings, "HTTPX_DEFAULT_TIMEOUT", 30.0))
    return httpx.Timeout(timeout_value)


def get_http_client(pool_name: str, timeout_sec: float | None = None) -> httpx.Client:
    if not pool_name:
        pool_name = "thirdparty_pool"

    with _LOCK:
        client = _CLIENTS.get(pool_name)
        if client is None:
            client = httpx.Client(limits=_resolve_limits(pool_name), timeout=_resolve_timeout(timeout_sec))
            _CLIENTS[pool_name] = client
            logger.info("[httpx] initialized pool=%s", pool_name)
            return client

    if timeout_sec is not None:
        client.timeout = _resolve_timeout(timeout_sec)
    return client


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
