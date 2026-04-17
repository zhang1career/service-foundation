from __future__ import annotations

import httpx
import json
import logging
import time
from django.conf import settings
from typing import Any, Dict, Optional

from common.services.http.client import get_http_client
from common.services.http.errors import HttpCallError
from common.services.http.outbound_url import (
    OutboundUrlPolicyError,
    sanitize_url_for_log,
    validate_outbound_http_url,
)
from common.services.http.pools import HttpClientPool, pool_id
from common.services.http.sync_task_ref import SYNC_HTTP_REQUEST_FN_REF

logger = logging.getLogger(__name__)


def request_sync(
        *,
        method: str,
        url: str,
        pool_name: HttpClientPool | str = HttpClientPool.THIRD_PARTY,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
        data: Any = None,
        timeout_sec: Optional[float] = None,
) -> httpx.Response:
    validate_outbound_http_url(url)

    pool_key = pool_id(pool_name)
    client = get_http_client(pool_name=pool_key, timeout_sec=timeout_sec)
    url_log = sanitize_url_for_log(url)
    start = time.perf_counter()
    try:
        response = client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            content=data,
            timeout=timeout_sec,
            follow_redirects=False,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[http_call] mode=sync pool=%s method=%s status=%s elapsed_ms=%s url=%s",
            pool_key,
            method.upper(),
            response.status_code,
            elapsed_ms,
            url_log,
        )
        return response
    except httpx.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "[http_call] mode=sync pool=%s method=%s error=%s elapsed_ms=%s url=%s",
            pool_key,
            method.upper(),
            type(exc).__name__,
            elapsed_ms,
            url_log,
        )
        raise HttpCallError(str(exc)) from exc


def request_async(
        *,
        method: str,
        url: str,
        pool_name: HttpClientPool | str = HttpClientPool.THIRD_PARTY,
        queue_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
        data: Any = None,
        timeout_sec: Optional[float] = None,
) -> str:
    from common.services.task import sync_call_task

    validate_outbound_http_url(url)

    pool_key = pool_id(pool_name)
    fn_kwargs = {
        "method": method.upper(),
        "url": url,
        "pool_name": pool_key,
        "headers": headers or {},
        "params": params or {},
        "json_body": json_body,
        "data": _normalize_data(data),
        "timeout_sec": timeout_sec,
    }
    queue = queue_name or _queue_for_pool(pool_key)
    task = sync_call_task.apply_async(
        kwargs={
            "sync_fn_ref": SYNC_HTTP_REQUEST_FN_REF,
            "fn_kwargs": fn_kwargs,
        },
        queue=queue,
    )
    url_log = sanitize_url_for_log(url)
    logger.info(
        "[http_call] mode=async pool=%s queue=%s method=%s task_id=%s url=%s",
        pool_key,
        queue,
        method.upper(),
        task.id,
        url_log,
    )
    return str(task.id)


def _queue_for_pool(pool_key: str) -> str:
    mapping = getattr(settings, "HTTPX_POOL_CELERY_QUEUE", None) or {}
    return mapping.get(
        pool_key,
        getattr(settings, "CELERY_TASK_DEFAULT_QUEUE", "default"),
    )


def _normalize_data(data: Any) -> Any:
    if isinstance(data, (bytes, bytearray)):
        return {"_type": "bytes", "value": bytes(data).decode("latin1")}
    if isinstance(data, str):
        return {"_type": "str", "value": data}
    if data is None:
        return None
    # Ensure async payload remains JSON serializable.
    return {"_type": "json", "value": json.loads(json.dumps(data))}
