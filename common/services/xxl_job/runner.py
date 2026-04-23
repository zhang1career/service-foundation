from __future__ import annotations

import logging
import traceback

from common.services.xxl_job.callback import send_callback
from common.services.xxl_job.registry import XxlJobRegistry

logger = logging.getLogger(__name__)

_MSG_CAP = 8000


def run_sync(
        *,
        registry: XxlJobRegistry,
        executor_handler: str,
        executor_params: str | None,
        log_id: int,
) -> tuple[bool, str]:
    """Run handler, POST callback to admin, return ``(ok, detail)`` for HTTP ``msg``."""

    def _callback_or_warn(handle_code: int, handle_msg: str) -> None:
        delivered = send_callback(
            log_id=log_id,
            handle_code=handle_code,
            handle_msg=handle_msg,
        )
        if not delivered:
            logger.warning(
                "[xxl_job] callback not delivered log_id=%s handler=%s handle_code=%s "
                "(set XXL_JOB_ADMIN_ADDRESS to admin base URL ending with /xxl-job-admin "
                "when applicable; token must match)",
                log_id,
                executor_handler,
                handle_code,
            )

    fn = registry.get(executor_handler)
    if fn is None:
        detail = f"unknown handler: {executor_handler}"
        _callback_or_warn(500, detail)
        return False, detail
    try:
        ret = fn(executor_params)
    except Exception:
        logger.exception("[xxl_job] handler=%s", executor_handler)
        detail = traceback.format_exc()[:_MSG_CAP]
        _callback_or_warn(500, detail)
        return False, detail
    if not isinstance(ret, tuple) or len(ret) != 2:
        detail = "handler must return (bool, str)"
        _callback_or_warn(500, detail)
        return False, detail
    ok, msg = ret[0], ret[1]
    s = msg if isinstance(msg, str) else str(msg)
    if bool(ok):
        text = (s.strip() if s else "") or "OK"
        out = text[:_MSG_CAP]
        _callback_or_warn(200, out)
        return True, out
    detail = (s or "failed")[:_MSG_CAP]
    _callback_or_warn(500, detail)
    return False, detail
