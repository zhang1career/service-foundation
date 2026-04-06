from __future__ import annotations

import atexit
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

logger = logging.getLogger(__name__)

_EXECUTORS: Dict[str, ThreadPoolExecutor] = {}
_FIRST_MAX_WORKERS: Dict[str, int] = {}
_LOCK = threading.Lock()


def get_thread_pool_executor(name: str, *, max_workers: int) -> ThreadPoolExecutor:
    """Return a process-wide (lazy) pool for ``name``.

    The first call for ``name`` creates ``ThreadPoolExecutor`` with the given
    ``max_workers``. Later calls with the same ``name`` return the same
    instance; if ``max_workers`` differs, a warning is logged and the existing
    pool is unchanged.

    Prefer one callsite per ``name`` (e.g. app settings) so ``max_workers`` is
    stable. Use :func:`shutdown_thread_pool_executors` on graceful shutdown if
    needed; otherwise ``atexit`` runs ``shutdown(wait=False)``.
    """
    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")
    with _LOCK:
        existing = _EXECUTORS.get(name)
        if existing is not None:
            first = _FIRST_MAX_WORKERS.get(name)
            if first is not None and first != max_workers:
                logger.warning(
                    "[thread_pool] ignoring max_workers=%s for name=%s (pool uses %s)",
                    max_workers,
                    name,
                    first,
                )
            return existing

        ex = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"{name}_")
        _EXECUTORS[name] = ex
        _FIRST_MAX_WORKERS[name] = max_workers
        logger.info("[thread_pool] initialized name=%s max_workers=%s", name, max_workers)
        return ex


def shutdown_thread_pool_executors(*, wait: bool = False) -> None:
    """Close all pools created via :func:`get_thread_pool_executor`."""
    with _LOCK:
        for pool_name, ex in list(_EXECUTORS.items()):
            try:
                ex.shutdown(wait=wait)
                logger.info("[thread_pool] shutdown name=%s wait=%s", pool_name, wait)
            except Exception:
                logger.exception("[thread_pool] shutdown failed name=%s", pool_name)
        _EXECUTORS.clear()
        _FIRST_MAX_WORKERS.clear()


def _atexit_shutdown() -> None:
    shutdown_thread_pool_executors(wait=False)


atexit.register(_atexit_shutdown)
