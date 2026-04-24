from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from django.conf import settings

from common.consts.response_const import RET_OK
from common.services.http import HttpClientPool, request_sync
from common.services.service_discovery import maybe_expand_service_discovery_url
from common.utils.json_util import API_JSON_DUMPS_PARAMS, json_decode
from common.utils.service_url_template import ServiceUrlResolutionError

logger = logging.getLogger(__name__)


def call_saga_endpoint(
        *,
        url: str,
        json_body: dict[str, Any],
        timeout_sec: float | None = None,
) -> tuple[int, str, dict[str, Any] | None]:
    """
    POST JSON. Returns (http_status, error_snippet, parsed_json_or_none).
    On HTTP success, if body is JSON object with errorCode, requires RET_OK for logical success.
    """
    try:
        url = maybe_expand_service_discovery_url(url)
    except ServiceUrlResolutionError as e:
        logger.warning("saga service URL unresolved: %s", e)
        return 0, str(e)[:500], None

    timeout = float(timeout_sec if timeout_sec is not None else settings.SAGA_OUTBOUND_TIMEOUT_SEC)
    try:
        resp = request_sync(
            method="POST",
            url=url,
            json_body=json_body,
            pool_name=HttpClientPool.THIRD_PARTY,
            timeout_sec=timeout,
        )
    except httpx.HTTPError as e:
        logger.warning("saga outbound call failed url=%s err=%s", url, e)
        return 0, str(e)[:500], None

    snippet = (resp.text or "")[:500]
    if not (200 <= resp.status_code < 300):
        return resp.status_code, snippet, None

    try:
        data = resp.json()
    except ValueError:
        return resp.status_code, "", None

    if isinstance(data, dict) and "errorCode" in data:
        if int(data.get("errorCode", -1)) != RET_OK:
            msg = data.get("message") or "errorCode != 0"
            return resp.status_code, str(msg)[:500], data
    return resp.status_code, "", data if isinstance(data, dict) else None


def merge_context_from_response(context: dict[str, Any], resp_obj: dict[str, Any] | None) -> None:
    if not resp_obj:
        return
    inner = resp_obj.get("data")
    if isinstance(inner, dict):
        for k, v in inner.items():
            context[k] = v


def dumps_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, **API_JSON_DUMPS_PARAMS)


def loads_json_dict(raw: str | None) -> dict[str, Any]:
    """
    Parse *raw* as a JSON object. Invalid JSON, empty text, ``null`` / missing
    document, or a non-object root raises ``ValueError``; non-``str`` input
    (except ``None``) raises ``TypeError`` (from :func:`json_decode`).
    """
    data = json_decode(raw)
    if data is None:
        raise ValueError("loads_json_dict: JSON document is null or missing")
    if not isinstance(data, dict):
        raise ValueError("loads_json_dict: JSON root must be an object")
    return data
