import hashlib
import json
import logging
import re
import uuid
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from typing import Any, Optional

from app_aibroker.consts.multimodal_const import (
    AIBROKER_MM_ALLOWED_MIMES,
)
from app_aibroker.services.aibroker_oss_http_service import put_uploaded_file

logger = logging.getLogger(__name__)

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def _digest_uploaded_file(f: UploadedFile) -> str:
    h = hashlib.sha256()
    if hasattr(f, "seek"):
        f.seek(0)
    for chunk in f.chunks():
        h.update(chunk)
    if hasattr(f, "seek"):
        f.seek(0)
    return h.hexdigest()


def _sanitize_filename(name: str) -> str:
    base = (name or "file").split("/")[-1].split("\\")[-1]
    base = _SAFE_NAME.sub("_", base)[:120]
    return base or "file"


def upload_one_aibroker_file(uploaded: UploadedFile) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """
    Validate and upload a single multipart file to app_oss via HTTP PUT.

    Returns ({url, mime_type, sha256, object_key, original_name}, None) or (None, error_message).
    """
    mime = (uploaded.content_type or "").strip().lower()
    if not mime or mime not in AIBROKER_MM_ALLOWED_MIMES:
        return None, f"unsupported or missing content type: {mime or 'empty'}"

    size = int(uploaded.size or 0)
    if size <= 0:
        return None, "empty file"
    if size > settings.AIBROKER_MM_MAX_BYTES_PER_FILE:
        return None, f"file too large (max {settings.AIBROKER_MM_MAX_BYTES_PER_FILE} bytes)"

    sha256 = _digest_uploaded_file(uploaded)
    safe = _sanitize_filename(uploaded.name)
    obj_key = f"aibroker/mm/{uuid.uuid4().hex}_{safe}"
    try:
        url = put_uploaded_file(uploaded, obj_key, mime)
    except RuntimeError:
        logger.exception("[aibroker] app_oss HTTP upload failed key=%s", obj_key)
        return None, "failed to store file"

    return (
        {
            "url": url,
            "mime_type": mime,
            "sha256": sha256,
            "object_key": obj_key,
            "original_name": uploaded.name or "",
        },
        None,
    )


def parse_meta_json(meta_raw: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    if meta_raw is None or not str(meta_raw).strip():
        return None, "missing meta"
    try:
        obj = json.loads(meta_raw)
    except json.JSONDecodeError:
        return None, "invalid meta JSON"
    if not isinstance(obj, dict):
        return None, "meta must be a JSON object"
    return obj, None
