"""
Structured request/response logging for all HTTP traffic.

Uses ``settings.HTTP_REQUEST_LOG_LOGGER`` (logger name). Configure the logger
in ``LOGGING`` (e.g. level and handlers).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from django.conf import settings
from django.template.response import ContentNotRenderedError
from django.utils.deprecation import MiddlewareMixin

_MAX_BODY_JSON_CHARS = 8192
_MAX_RESPONSE_JSON_CHARS = 4096
_MAX_STR_PREVIEW = 200


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
    def __init__(self, get_response):
        super().__init__(get_response)
        self._logger_name = (getattr(settings, "HTTP_REQUEST_LOG_LOGGER", None) or "").strip() or "http.request"

    def process_request(self, request):
        request._http_request_log_start = time.perf_counter()
        _log_request(self._logger_name, request)
        return None

    def process_response(self, request, response):
        _log_response(self._logger_name, request, response)
        return response
