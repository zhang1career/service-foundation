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
) -> None:
    fn = registry.get(executor_handler)
    if fn is None:
        send_callback(
            log_id=log_id,
            handle_code=500,
            handle_msg=f"unknown handler: {executor_handler}",
        )
        return
    try:
        ret = fn(executor_params)
    except Exception:
        logger.exception("[xxl_job] handler=%s", executor_handler)
        send_callback(
            log_id=log_id,
            handle_code=500,
            handle_msg=traceback.format_exc()[:_MSG_CAP],
        )
        return
    if not isinstance(ret, tuple) or len(ret) != 2:
        send_callback(
            log_id=log_id,
            handle_code=500,
            handle_msg="handler must return (bool, str)",
        )
        return
    ok, msg = ret[0], ret[1]
    s = msg if isinstance(msg, str) else str(msg)
    send_callback(
        log_id=log_id,
        handle_code=200 if bool(ok) else 500,
        handle_msg=s[:_MSG_CAP] if s else "",
    )
