"""
HTTP transport for this service's public API (outbound calls to the same contract).

Not in ``common``: avoids ``common`` depending on AIBroker URLs, credentials, or
``RET_OK`` semantics for this microservice.
"""
import uuid
from typing import Any, Dict, Optional

from common.consts.response_const import RET_OK
from common.services.http import HttpClientPool, request_sync

TEXT_GENERATE_PATH = "/v1/text/generate"
EMBEDDINGS_PATH = "/v1/embeddings"
DEFAULT_TIMEOUT_SEC = 120


def _resolve_root_and_key() -> tuple[str, str]:
    root = setting_str("AIBROKER_SERVICE_URL", "").rstrip("/")
    key = setting_str("KNOW_AIBROKER_ACCESS_KEY", "")
    if not root or not key:
        raise RuntimeError("AIBROKER_SERVICE_URL and KNOW_AIBROKER_ACCESS_KEY must be set")
    return root, key


def _post_to_path(
    path: str,
    payload: Dict[str, Any],
    *,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    root, key = _resolve_root_and_key()
    url = f"{root}{path}"
    body = {**payload, "access_key": key}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Correlation-Id": str(uuid.uuid4()),
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    resp = request_sync(
        method="POST",
        url=url,
        pool_name=HttpClientPool.THIRD_PARTY,
        json_body=body,
        headers=headers,
        timeout_sec=DEFAULT_TIMEOUT_SEC,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"aibroker HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    if not data or data.get("errorCode") != RET_OK:
        raise RuntimeError((data or {}).get("message") or "aibroker error")
    return data.get("data") or {}


def aibroker_http_post(payload: Dict[str, Any], *, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """
    POST to AIBroker text-generate endpoint.
    """
    return _post_to_path(TEXT_GENERATE_PATH, payload, idempotency_key=idempotency_key)


def aibroker_http_post_embeddings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    POST to AIBroker embeddings endpoint.
    """
    return _post_to_path(EMBEDDINGS_PATH, payload)
