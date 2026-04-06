import importlib
import logging
import time
from typing import Any, Dict

from celery import shared_task

from common.services.http.errors import HttpCallError

logger = logging.getLogger(__name__)


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
    return {
        "status_code": status_code,
        "headers": dict(getattr(result, "headers", {})),
        "text": getattr(result, "text", ""),
        "url": str(getattr(result, "request").url),
        "elapsed_ms": elapsed_ms,
    }
