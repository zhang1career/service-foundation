"""
Structured access logging for app_tcc and app_saga HTTP APIs (entry + exit + duration).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from django.utils.deprecation import MiddlewareMixin

from common.utils.http_util import resolve_request_id

_TCC_PREFIX = "/api/tcc/"
_SAGA_PREFIX = "/api/saga/"
_MAX_BODY_JSON_CHARS = 8192
_MAX_RESPONSE_JSON_CHARS = 4096
_MAX_DATA_PREVIEW_ITEMS = 5
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
        keys = list(value.keys())
        if len(keys) > _MAX_DATA_PREVIEW_ITEMS:
            return {
                "_keys_sample": keys[:_MAX_DATA_PREVIEW_ITEMS],
                "_key_count": len(keys),
            }
        return {k: _abbreviate_value(value[k]) for k in keys}
    return repr(value)[:_MAX_STR_PREVIEW]


def _request_params_snapshot(request) -> dict[str, Any]:
    out: dict[str, Any] = {"method": request.method, "path": request.get_full_path()}
    out["query"] = dict(request.GET)
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


def _response_payload_summary(response) -> tuple[Any, Any, Any]:
    try:
        text = response.content.decode("utf-8", errors="replace")
    except Exception:
        return None, None, "<no_content>"
    if len(text) > _MAX_RESPONSE_JSON_CHARS:
        text = text[:_MAX_RESPONSE_JSON_CHARS] + "…"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, None, "<non_json_response>"
    ec = payload.get("errorCode")
    msg = payload.get("message")
    data = _abbreviate_value(payload.get("data"))
    return ec, msg, data


class TccSagaAccessLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path or ""
        if not (path.startswith(_TCC_PREFIX) or path.startswith(_SAGA_PREFIX)):
            return None
        request._tcc_saga_access_start = time.perf_counter()
        trace_id = resolve_request_id(request)
        params = _request_params_snapshot(request)
        if path.startswith(_TCC_PREFIX):
            logging.getLogger("app_tcc.access").info(
                "request_in trace_id=%s params=%s",
                trace_id,
                params,
            )
        else:
            logging.getLogger("app_saga.access").info(
                "request_in trace_id=%s params=%s",
                trace_id,
                params,
            )
        return None

    def process_response(self, request, response):
        path = request.path or ""
        if not (path.startswith(_TCC_PREFIX) or path.startswith(_SAGA_PREFIX)):
            return response
        start = getattr(request, "_tcc_saga_access_start", None)
        duration_ms = None
        if start is not None:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
        trace_id = resolve_request_id(request)
        ec, msg, data = _response_payload_summary(response)
        if path.startswith(_TCC_PREFIX):
            logging.getLogger("app_tcc.access").info(
                "request_out trace_id=%s errorCode=%s message=%s data=%s duration_ms=%s status=%s",
                trace_id,
                ec,
                msg,
                data,
                duration_ms,
                getattr(response, "status_code", None),
            )
        else:
            logging.getLogger("app_saga.access").info(
                "request_out trace_id=%s errorCode=%s message=%s data=%s duration_ms=%s status=%s",
                trace_id,
                ec,
                msg,
                data,
                duration_ms,
                getattr(response, "status_code", None),
            )
        return response
