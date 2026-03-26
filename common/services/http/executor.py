import json
import logging
import time
from typing import Any, Dict, Optional

import httpx
from django.conf import settings

from common.services.http.client import get_http_client

logger = logging.getLogger(__name__)


class HttpCallError(RuntimeError):
    pass


def request_sync(
    *,
    method: str,
    url: str,
    pool_name: str = "thirdparty_pool",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    data: Any = None,
    timeout_sec: Optional[float] = None,
) -> httpx.Response:
    client = get_http_client(pool_name=pool_name, timeout_sec=timeout_sec)
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
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "[http_call] mode=sync pool=%s method=%s status=%s elapsed_ms=%s url=%s",
            pool_name,
            method.upper(),
            response.status_code,
            elapsed_ms,
            url,
        )
        return response
    except httpx.HTTPError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "[http_call] mode=sync pool=%s method=%s error=%s elapsed_ms=%s url=%s",
            pool_name,
            method.upper(),
            type(exc).__name__,
            elapsed_ms,
            url,
        )
        raise HttpCallError(str(exc)) from exc


def request_async(
    *,
    method: str,
    url: str,
    pool_name: str = "thirdparty_pool",
    queue_name: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    data: Any = None,
    timeout_sec: Optional[float] = None,
) -> str:
    from common.tasks.http_tasks import execute_http_request_task

    payload = {
        "method": method.upper(),
        "url": url,
        "pool_name": pool_name,
        "headers": headers or {},
        "params": params or {},
        "json_body": json_body,
        "data": _normalize_data(data),
        "timeout_sec": timeout_sec,
    }
    queue = queue_name or _queue_for_pool(pool_name)
    task = execute_http_request_task.apply_async(kwargs=payload, queue=queue)
    logger.info(
        "[http_call] mode=async pool=%s queue=%s method=%s task_id=%s url=%s",
        pool_name,
        queue,
        method.upper(),
        task.id,
        url,
    )
    return str(task.id)


def _queue_for_pool(pool_name: str) -> str:
    if pool_name == "avatar_http_pool":
        return "avatar"
    if pool_name == "webhook_pool":
        return "webhook"
    if pool_name == "thirdparty_pool":
        return "thirdparty"
    return getattr(settings, "CELERY_TASK_DEFAULT_QUEUE", "default")


def _normalize_data(data: Any) -> Any:
    if isinstance(data, (bytes, bytearray)):
        return {"_type": "bytes", "value": bytes(data).decode("latin1")}
    if isinstance(data, str):
        return {"_type": "str", "value": data}
    if data is None:
        return None
    # Ensure async payload remains JSON serializable.
    return {"_type": "json", "value": json.loads(json.dumps(data))}
