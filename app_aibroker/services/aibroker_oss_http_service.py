"""
Upload AI Broker multimodal files to app_oss via HTTP (S3-compatible PUT).

Must use HTTP to OSS; do not call app_oss Python APIs from here (service boundary).
"""

import logging
from django.conf import settings
from typing import Any
from urllib.parse import quote

from common.services.http import HttpCallError, HttpClientPool, request_sync

logger = logging.getLogger(__name__)

_PUT_TIMEOUT_SEC = 120


def _read_upload_body(file_obj: Any) -> bytes:
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except OSError:
            pass
    chunks: list[bytes] = []
    if hasattr(file_obj, "chunks"):
        for part in file_obj.chunks():
            chunks.append(part)
    else:
        chunks.append(file_obj.read())
    if hasattr(file_obj, "seek"):
        try:
            file_obj.seek(0)
        except OSError:
            pass
    return b"".join(chunks)


def put_object_http(object_key: str, body: bytes, content_type: str) -> str:
    """
    PUT object to app_oss. Returns absolute URL of the object (same path used for GET).
    """
    base = str(getattr(settings, "AIBROKER_OSS_ENDPOINT", "") or "").rstrip("/")
    bucket = str(getattr(settings, "AIBROKER_OSS_BUCKET", "") or "").strip()
    if not base or not bucket:
        raise RuntimeError("AIBROKER_OSS_ENDPOINT and AIBROKER_OSS_BUCKET must be configured")

    url = f"{base}/{bucket}/{quote(object_key, safe='/')}"
    logger.info(
        "[aibroker_oss_http] PUT bytes=%s content_type=%s url=%s",
        len(body),
        content_type,
        url,
    )
    try:
        resp = request_sync(
            method="PUT",
            url=url,
            pool_name=HttpClientPool.THIRD_PARTY,
            data=body,
            headers={"Content-Type": content_type},
            timeout_sec=_PUT_TIMEOUT_SEC,
        )
    except HttpCallError as exc:
        logger.exception("[aibroker_oss_http] PUT failed url=%s", url)
        raise RuntimeError(f"oss put failed: {exc}") from exc

    if resp.status_code != 200:
        preview = (resp.text or "")[:300]
        logger.error(
            "[aibroker_oss_http] bad status=%s url=%s body=%r",
            resp.status_code,
            url,
            preview,
        )
        raise RuntimeError(f"oss put rejected: HTTP {resp.status_code}")

    return url


def put_uploaded_file(uploaded_file, object_key: str, content_type: str) -> str:
    data = _read_upload_body(uploaded_file)
    return put_object_http(object_key, data, content_type)
