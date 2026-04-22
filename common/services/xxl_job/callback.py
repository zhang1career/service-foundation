"""POST result to XXL-JOB admin ``/api/callback``."""

from __future__ import annotations

import logging
import time
from typing import Any

from django.conf import settings

from common.services.http.errors import HttpCallError
from common.services.http.executor import request_sync
from common.services.http.pools import HttpClientPool
from common.utils.service_url_template import (
    ServiceUrlResolutionError,
    expand_service_url_from_env,
)

logger = logging.getLogger(__name__)


def _admin_base() -> str:
    raw = (getattr(settings, "XXL_JOB_ADMIN_ADDRESS", "") or "").strip()
    if not raw:
        return ""
    if "://{{" in raw:
        try:
            raw = expand_service_url_from_env(raw)
        except ServiceUrlResolutionError as e:
            logger.warning("[xxl_job] XXL_JOB_ADMIN_ADDRESS unresolved: %s", e)
            return ""
    return raw.rstrip("/")


def send_callback(*, log_id: int, handle_code: int, handle_msg: str) -> bool:
    base = _admin_base()
    if not base:
        logger.warning("[xxl_job] no admin address; skip callback log_id=%s", log_id)
        return False
    token = (getattr(settings, "XXL_JOB_TOKEN", "") or "").strip()
    if not token:
        logger.warning("[xxl_job] no token; skip callback log_id=%s", log_id)
        return False

    url = f"{base}/api/callback"
    timeout = float(getattr(settings, "XXL_JOB_CALLBACK_TIMEOUT_SEC", 10.0))
    body: list[dict[str, Any]] = [
        {
            "logId": log_id,
            "logDateTim": int(time.time() * 1000),
            "handleCode": int(handle_code),
            "handleMsg": handle_msg or "",
        }
    ]
    headers = {
        "Content-Type": "application/json",
        "XXL-JOB-ACCESS-TOKEN": token,
    }
    try:
        resp = request_sync(
            method="POST",
            url=url,
            pool_name=HttpClientPool.WEBHOOK,
            headers=headers,
            json_body=body,
            timeout_sec=timeout,
        )
    except HttpCallError as e:
        logger.error("[xxl_job] callback HTTP error log_id=%s: %s", log_id, e)
        return False
    if resp.status_code != 200:
        logger.error(
            "[xxl_job] callback status=%s log_id=%s body=%s",
            resp.status_code,
            log_id,
            (resp.text or "")[:500],
        )
        return False
    return True
