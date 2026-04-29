"""
Structured request/response logging for all HTTP traffic.

Uses the same top-level loggers as the rest of the project: the resolved view’s
``__module__`` yields the logger name (e.g. ``app_user.views.x`` → ``app_user``,
``common.views.x`` → ``common``). That matches ``LOGGING`` handlers for each
``app_*`` / ``common`` / ``service_foundation``. Unresolvable paths and views
under ``django.*`` / ``rest_framework.*`` use ``HTTP_REQUEST_LOG_FALLBACK_LOGGER``.
"""

from __future__ import annotations

import functools
import json
import logging
import time
from typing import Any

from django.template.response import ContentNotRenderedError
from django.urls import Resolver404, resolve
from django.utils.deprecation import MiddlewareMixin

from common.utils.django_util import setting_str

_MAX_BODY_JSON_CHARS = 8192
_MAX_RESPONSE_JSON_CHARS = 4096
_MAX_STR_PREVIEW = 200


def _fallback_logger_name() -> str:
    return setting_str("HTTP_REQUEST_LOG_FALLBACK_LOGGER", "service_foundation")


def _callable_module_name(callable_obj: Any) -> str:
    inner: Any = callable_obj
    while isinstance(inner, functools.partial):
        inner = inner.func
    return (getattr(inner, "__module__", None) or "").strip()


def _logger_name_from_view_module(module_name: str) -> str | None:
    if not module_name or module_name.startswith("django.") or module_name.startswith("rest_framework."):
        return None
    head = module_name.split(".", 1)[0]
    if head == "common" or head.startswith("app_") or head == "service_foundation":
        return head
    return None


def _logger_name_from_resolver_match(match) -> str:
    mod = _callable_module_name(match.func)
    resolved = _logger_name_from_view_module(mod)
    if resolved is not None:
        return resolved
    return _fallback_logger_name()


def resolve_http_request_log_logger(path_info: str, *, urlconf: str | None = None) -> str:
    """
    Map *path_info* to a configured project logger via ``django.urls.resolve``,
    or return ``HTTP_REQUEST_LOG_FALLBACK_LOGGER``.
    """
    p = (path_info or "/").strip()
    if not p.startswith("/"):
        p = "/" + p
    try:
        match = resolve(p, urlconf=urlconf)
    except Resolver404:
        return _fallback_logger_name()
    return _logger_name_from_resolver_match(match)


def resolve_http_request_log_logger_for_request(request) -> str:
    path_info = getattr(request, "path_info", None) or getattr(request, "path", "") or "/"
    urlconf = getattr(request, "urlconf", None)
    return resolve_http_request_log_logger(path_info, urlconf=urlconf)


def _abbreviate_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) > _MAX_STR_PREVIEW:
            return value[:_MAX_STR_PREVIEW] + "…"
        return value
    if isinstance(value, list):
        if not value:
            return []
        head = [_abbreviate_value(value[i]) for i in range(min(3, len(value)))]
        if len(value) > 3:
            return {"_len": len(value), "_head": head}
        return head
    if isinstance(value, dict):
        return {k: _abbreviate_value(value[k]) for k in value.keys()}
    return repr(value)[:_MAX_STR_PREVIEW]


def _request_params_snapshot(request) -> dict[str, Any]:
    out: dict[str, Any] = {"method": request.method, "path": request.get_full_path(), "query": dict(request.GET)}
    if request.method not in ("POST", "PUT", "PATCH"):
        return out
    ct = (request.META.get("CONTENT_TYPE") or "").split(";")[0].strip().lower()
    out["content_type"] = ct or None
    if ct == "application/json":
        try:
            raw = request.body
            text = raw.decode("utf-8", errors="replace")
            if len(text) > _MAX_BODY_JSON_CHARS:
                out["body"] = {
                    "_truncated": True,
                    "preview": text[:_MAX_BODY_JSON_CHARS],
                }
            else:
                out["body"] = json.loads(text) if text else None
        except (json.JSONDecodeError, OSError, ValueError):
            out["body"] = "<json_parse_error>"
    elif request.POST:
        out["form"] = dict(list(request.POST.items())[:50])
    else:
        out["content_length"] = request.META.get("CONTENT_LENGTH")
    return out


def response_payload_summary(response) -> tuple[Any, Any, Any]:
    blob = getattr(response, "data", None)
    if isinstance(blob, dict) and "code" in blob:
        return (
            blob.get("code"),
            blob.get("msg"),
            _abbreviate_value(blob.get("data")),
        )
    try:
        raw = response.content
    except (AttributeError, OSError, TypeError, ContentNotRenderedError):
        return None, None, None
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return None, None, None
    if len(text) > _MAX_RESPONSE_JSON_CHARS:
        text = text[:_MAX_RESPONSE_JSON_CHARS] + "…"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, None, None
    if not isinstance(payload, dict):
        return None, None, None
    return (
        payload.get("code"),
        payload.get("msg"),
        _abbreviate_value(payload.get("data")),
    )


def _log_response(logger_name: str, request, response) -> None:
    start = getattr(request, "_http_request_log_start", None)
    duration_ms = None
    if start is not None:
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
    code, msg, data = response_payload_summary(response)

    logging.getLogger(logger_name).info(
        "%s code=%s msg=%s data=%s (%s)",
        getattr(response, "status_code", None),
        code,
        msg,
        data,
        duration_ms,
    )


def _log_request(logger_name: str, request) -> None:
    params = _request_params_snapshot(request)
    logging.getLogger(logger_name).info(
        "params=%s",
        params,
    )


class HttpRequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._http_request_log_start = time.perf_counter()
        name = resolve_http_request_log_logger_for_request(request)
        request._http_request_log_logger = name
        _log_request(name, request)
        return None

    def process_response(self, request, response):
        name = getattr(request, "_http_request_log_logger", None) or resolve_http_request_log_logger_for_request(
            request
        )
        _log_response(name, request, response)
        return response
