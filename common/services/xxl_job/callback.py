"""POST result to XXL-JOB admin ``/api/callback``."""

from __future__ import annotations

import json
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

# XXL-JOB ``ReturnT.SUCCESS_CODE`` (admin ``/api/*`` JSON envelope).
_RETURN_T_SUCCESS = 200


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
            "logDateTim": time.time_ns() // 1_000_000,
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
    raw_txt = getattr(resp, "text", "")
    text = (raw_txt if isinstance(raw_txt, str) else "").strip()
    if not text:
        logger.info("[xxl_job] callback accepted log_id=%s handle_code=%s", log_id, handle_code)
        return True
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        logger.info("[xxl_job] callback accepted log_id=%s (non-json response)", log_id)
        return True
    if isinstance(payload, dict):
        ret_code = payload.get("code")
        if ret_code is not None and int(ret_code) != _RETURN_T_SUCCESS:
            logger.error(
                "[xxl_job] callback admin ReturnT code=%s msg=%s log_id=%s",
                ret_code,
                (payload.get("msg") or "")[:500],
                log_id,
            )
            return False
    logger.info("[xxl_job] callback accepted log_id=%s handle_code=%s", log_id, handle_code)
    return True
