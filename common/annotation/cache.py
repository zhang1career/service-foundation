"""
Generic caching helpers (decorators play a similar role to Java annotations).

- ``django_cached``: store results in Django's cache backend (e.g. Redis).
- ``local_ttl_cached``: in-process TTL + LRU via cachetools (Guava-like local cache).

Limitation: if the wrapped function legitimately returns ``None``, Django cache
and TTLCache may treat it like a miss; use a sentinel or avoid caching None.
"""
from __future__ import annotations

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional, TypeVar


F = TypeVar("F", bound=Callable[..., Any])


def _args_key(func_qualname: str, args: tuple, kwargs: dict) -> str:
    try:
        payload = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    except TypeError:
        payload = str((args, kwargs))
    digest = hashlib.sha256(payload.encode()).hexdigest()[:32]
    return f"{func_qualname}:{digest}"


def django_cached(
    *,
    key_prefix: str,
    ttl_seconds: int,
    cache_alias: str = "default",
    key_fn: Optional[Callable[..., str]] = None,
) -> Callable[[F], F]:
    """
    Cache synchronous function results in Django's cache.

    ``key_fn`` — optional ``(func, args, kwargs) -> str`` for the key body
    (after ``key_prefix``). Default uses a stable hash of arguments.
    """

    def decorator(func: F) -> F:
        from django.core.cache import caches

        qual = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            cache = caches[cache_alias]
            if key_fn is not None:
                key_body = key_fn(func, args, kwargs)
            else:
                key_body = _args_key(qual, args, kwargs)
            key = f"{key_prefix}:{key_body}"
            hit = cache.get(key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def local_ttl_cached(*, maxsize: int, ttl_seconds: float) -> Callable[[F], F]:
    """
    In-process TTL cache using cachetools.TTLCache (per decorated function).
    """

    def decorator(func: F) -> F:
        from cachetools import TTLCache

        store: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        qual = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            k = _args_key(qual, args, kwargs)
            if k in store:
                return store[k]
            result = func(*args, **kwargs)
            store[k] = result
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
