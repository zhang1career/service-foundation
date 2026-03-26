import logging
import time
from typing import Any, Dict, Optional

from celery import shared_task

from common.services.http.executor import HttpCallError, request_sync

logger = logging.getLogger(__name__)


def _restore_data(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    dtype = data.get("_type")
    if dtype == "bytes":
        return (data.get("value") or "").encode("latin1")
    if dtype == "str":
        return data.get("value") or ""
    if dtype == "json":
        return data.get("value")
    return data


@shared_task(
    bind=True,
    autoretry_for=(HttpCallError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def execute_http_request_task(
    self,
    *,
    method: str,
    url: str,
    pool_name: str = "thirdparty_pool",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    data: Any = None,
    timeout_sec: Optional[float] = None,
) -> Dict[str, Any]:
    start = time.perf_counter()
    resp = request_sync(
        method=method,
        url=url,
        pool_name=pool_name,
        headers=headers,
        params=params,
        json_body=json_body,
        data=_restore_data(data),
        timeout_sec=timeout_sec,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    out = {
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "text": resp.text,
        "url": str(resp.request.url),
        "elapsed_ms": elapsed_ms,
    }
    logger.info(
        "[http_task] pool=%s method=%s status=%s elapsed_ms=%s task_id=%s",
        pool_name,
        method,
        resp.status_code,
        elapsed_ms,
        self.request.id,
    )
    return out
