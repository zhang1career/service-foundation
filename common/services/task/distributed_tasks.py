import importlib
import logging
import time
from typing import Any, Dict

from celery import shared_task
from django.conf import settings

from common.services.http.errors import HttpCallError
from common.services.http.outbound_url import sanitize_url_for_log
from common.services.http.sync_task_ref import SYNC_HTTP_REQUEST_FN_REF

logger = logging.getLogger(__name__)


def _allowed_sync_fn_refs() -> frozenset[str]:
    configured = getattr(settings, "CELERY_SYNC_CALL_ALLOWED_REFS", None)
    if configured is not None:
        return frozenset(configured)
    return frozenset({SYNC_HTTP_REQUEST_FN_REF})


def _reject_if_sync_fn_ref_not_allowed(sync_fn_ref: str) -> None:
    if sync_fn_ref not in _allowed_sync_fn_refs():
        raise ValueError(f"sync_fn_ref is not allowed: {sync_fn_ref!r}")


@shared_task(
    bind=True,
    autoretry_for=(HttpCallError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def sync_call_task(
        self,
        *,
        sync_fn_ref: str,
        fn_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    _reject_if_sync_fn_ref_not_allowed(sync_fn_ref)
    sync_fn = _import_callable(sync_fn_ref)
    kwargs = dict(fn_kwargs)
    if "data" in kwargs:
        kwargs["data"] = _restore_payload_data(kwargs["data"])
    start = time.perf_counter()
    result = sync_fn(**kwargs)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    out = _result_to_dict(result, elapsed_ms)
    logger.info(
        "[sync_call_task] ref=%s elapsed_ms=%s task_id=%s",
        sync_fn_ref,
        elapsed_ms,
        self.request.id,
    )
    return out


def _import_callable(ref: str):
    """Resolve ``module:qualname`` to a callable (qualname may contain dots)."""
    if ref.count(":") != 1:
        raise ValueError(f"sync_fn_ref must be 'module:qualname', got {ref!r}")
    mod_path, qualname = ref.split(":", 1)
    module = importlib.import_module(mod_path)
    obj = module
    for attr in qualname.split("."):
        obj = getattr(obj, attr)
    if not callable(obj):
        raise TypeError(f"sync_fn_ref is not callable: {ref!r}")
    return obj


def _restore_payload_data(data: Any) -> Any:
    """Decode ``data`` values produced by :func:`common.services.http.executor._normalize_data`."""
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


def _result_to_dict(result: Any, elapsed_ms: int) -> Dict[str, Any]:
    if isinstance(result, dict):
        out = dict(result)
        out.setdefault("elapsed_ms", elapsed_ms)
        return out
    status_code = getattr(result, "status_code", None)
    if status_code is None:
        raise TypeError(
            "sync call result must be a dict or an object with status_code, headers, text, request"
        )
    raw_url = str(getattr(result, "request").url)
    return {
        "status_code": status_code,
        "headers": dict(getattr(result, "headers", {})),
        "text": getattr(result, "text", ""),
        "url": sanitize_url_for_log(raw_url),
        "elapsed_ms": elapsed_ms,
    }
