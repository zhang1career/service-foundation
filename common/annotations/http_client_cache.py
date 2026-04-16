from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.http import HttpResponseBase
from django.utils.cache import patch_cache_control
from django.utils.http import http_date

_ViewCallable = Callable[..., HttpResponseBase]


def apply_http_client_cache_headers(response: HttpResponseBase, max_age_seconds: int) -> None:
    """
    Set ``Cache-Control: max-age=…`` and a matching HTTP-date ``Expires`` on the response.
    """
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be >= 0")
    patch_cache_control(response, max_age=max_age_seconds)
    response["Expires"] = http_date(time.time() + max_age_seconds)


def _effective_max_age_seconds(ttl_seconds: int | None) -> int:
    """
    If ``ttl_seconds`` is not None and greater than 0, return it; otherwise read
    ``settings.HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS`` (populated from env at process start only).
    """
    if ttl_seconds is not None and ttl_seconds > 0:
        return ttl_seconds
    return int(settings.HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS)


def http_response_client_cache(
        view_or_ttl_seconds: _ViewCallable | int | None = None,
) -> _ViewCallable | Callable[[_ViewCallable], _ViewCallable]:
    """
    View decorator: after the view returns, set ``Cache-Control: max-age`` and ``Expires``.

    - ``@http_response_client_cache`` / ``@http_response_client_cache()`` — use
      ``settings.HTTP_RESPONSE_CACHE_MAX_AGE_SECONDS`` (from env at startup).
    - ``@http_response_client_cache(300)`` — if the integer is greater than ``0``, use it as
      max-age in seconds; does not read or modify environment variables at runtime.
    - ``@http_response_client_cache(0)`` — treated like no override (uses the setting above).

    For class-based views, wrap ``dispatch`` with ``django.utils.decorators.method_decorator``.
    """

    def _wrap(fn: _ViewCallable, ttl_seconds: int | None) -> _ViewCallable:
        @wraps(fn)
        def _wrapped(*args: Any, **kwargs: Any) -> HttpResponseBase:
            response = fn(*args, **kwargs)
            apply_http_client_cache_headers(response, _effective_max_age_seconds(ttl_seconds))
            return response

        return _wrapped

    if callable(view_or_ttl_seconds):
        return _wrap(view_or_ttl_seconds, None)

    if view_or_ttl_seconds is not None and not isinstance(view_or_ttl_seconds, int):
        raise TypeError(
            "http_response_client_cache expects a bare view or an int ttl (seconds); "
            f"got {type(view_or_ttl_seconds).__name__}",
        )

    ttl: int | None = view_or_ttl_seconds if isinstance(view_or_ttl_seconds, int) else None

    def decorator(fn: _ViewCallable) -> _ViewCallable:
        return _wrap(fn, ttl)

    return decorator
