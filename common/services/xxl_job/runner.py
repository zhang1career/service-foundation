from __future__ import annotations

import json
import logging
import traceback
from typing import Any

from common.services.xxl_job.callback import send_callback
from common.services.xxl_job.registry import XxlJobRegistry
from common.utils.json_util import API_JSON_DUMPS_PARAMS

logger = logging.getLogger(__name__)

_MSG_CAP = 8000


def _handle_msg_for_callback(payload: Any) -> str:
    """Match Paganini: ``json_encode($data)`` for admin callback ``handleMsg``."""
    if isinstance(payload, (dict, list, tuple)):
        try:
            return json.dumps(payload, default=str, **API_JSON_DUMPS_PARAMS)[:_MSG_CAP]
        except (TypeError, ValueError):
            return str(payload)[:_MSG_CAP]
    s = str(payload).strip() if payload is not None else ""
    return (s or "OK")[:_MSG_CAP]


def run_sync(
        *,
        registry: XxlJobRegistry,
        executor_handler: str,
        executor_params: str | None,
        log_id: int,
) -> tuple[bool, Any]:
    """Run handler, POST callback; return ``(ok, detail)`` for HTTP (``msg`` or ``data``)."""

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
        detail = "handler must return (bool, detail)"
        _callback_or_warn(500, detail)
        return False, detail
    ok, payload = ret[0], ret[1]
    if bool(ok):
        _callback_or_warn(200, _handle_msg_for_callback(payload))
        return True, payload
    err_text = str(payload).strip() if payload is not None else ""
    detail = (err_text or "failed")[:_MSG_CAP]
    _callback_or_warn(500, detail)
    return False, detail
