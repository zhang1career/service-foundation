from __future__ import annotations

import logging
from typing import Any

import httpx
from django.conf import settings

from app_tcc.enums import CancelReason
from common.services.http import HttpClientPool, request_sync
from common.services.service_discovery import maybe_expand_service_discovery_url
from common.utils.service_url_template import ServiceUrlResolutionError

logger = logging.getLogger(__name__)

PHASE_TRY = "try"
PHASE_CONFIRM = "confirm"
PHASE_CANCEL = "cancel"


def call_participant(
        *,
        url: str,
        phase: str,
        global_tx_id: str,
        branch_id: str,
        idempotency_key: str,
        payload: dict[str, Any] | None,
        cancel_reason: int | None = None,
) -> tuple[int, str]:
    """
    POST JSON to participant. Returns (http_status, error_or_body_snippet).
    Success: status in 200..299 and empty error string.

    For ``phase == \"cancel\"``, ``cancel_reason`` is required (int enum); omitted uses
    :data:`CancelReason.UNPAID`.
    """
    try:
        url = maybe_expand_service_discovery_url(url)
    except ServiceUrlResolutionError as e:
        logger.warning("tcc participant URL unresolved: %s", e)
        return 0, str(e)[:500]

    body: dict[str, Any] = {
        "global_tx_id": global_tx_id,
        "branch_id": branch_id,
        "phase": phase,
        "idempotency_key": idempotency_key,
        "payload": payload if payload is not None else {},
    }
    if phase == PHASE_CANCEL:
        body["cancel_reason"] = (
            int(cancel_reason) if cancel_reason is not None else CancelReason.UNPAID
        )
    timeout = float(settings.TCC_OUTBOUND_TIMEOUT_SEC)
    try:
        resp = request_sync(
            method="POST",
            url=url,
            json_body=body,
            pool_name=HttpClientPool.THIRD_PARTY,
            timeout_sec=timeout,
        )
    except httpx.HTTPError as e:
        logger.warning("participant call failed phase=%s url=%s err=%s", phase, url, e)
        return 0, str(e)[:500]

    snippet = (resp.text or "")[:500]
    if 200 <= resp.status_code < 300:
        return resp.status_code, ""
    return resp.status_code, snippet


def is_success_status(http_status: int) -> bool:
    return 200 <= http_status < 300
