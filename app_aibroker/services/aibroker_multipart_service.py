import hashlib
import json
import logging
import re
import uuid
from typing import Any, Optional

from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest

from app_aibroker.consts.multimodal_const import (
    AIBROKER_MM_ALLOWED_MIMES,
    AIBROKER_MM_MAX_BYTES_PER_FILE,
    AIBROKER_MM_MAX_FILES_TOTAL,
    VARIABLE_KINDS_MEDIA,
)
from app_aibroker.services.aibroker_oss_http_service import put_uploaded_file
from app_aibroker.services.template_render_service import parse_param_specs

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
    if size > AIBROKER_MM_MAX_BYTES_PER_FILE:
        return None, f"file too large (max {AIBROKER_MM_MAX_BYTES_PER_FILE} bytes)"

    sha256 = _digest_uploaded_file(uploaded)
    safe = _sanitize_filename(uploaded.name)
    obj_key = f"aibroker/mm/{uuid.uuid4().hex}_{safe}"
    try:
        url = put_uploaded_file(uploaded, obj_key, mime)
    except Exception:
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


def _upload_list(files: list[UploadedFile]) -> tuple[list[dict[str, Any]], Optional[str]]:
    out: list[dict[str, Any]] = []
    for f in files:
        item, err = upload_one_aibroker_file(f)
        if err:
            return [], err
        out.append(item)
    return out, None


def merge_multipart_attachments(
    request: HttpRequest,
    tpl_param_specs: Optional[str],
) -> tuple[list[dict[str, Any]], Optional[str]]:
    """
    Collect uploads from multipart: var_<name> for media param_specs, then field `files`.
    Order: media slots in spec order (each slot: all files for that name in upload order),
    then global `files` in upload order.
    """
    specs = parse_param_specs(tpl_param_specs)
    attachments: list[dict[str, Any]] = []

    for spec in specs:
        if spec.get("kind") not in VARIABLE_KINDS_MEDIA:
            continue
        name = spec.get("name")
        if not isinstance(name, str) or not name:
            continue
        key = f"var_{name}"
        chunk, err = _upload_list(list(request.FILES.getlist(key)))
        if err:
            return [], err
        attachments.extend(chunk)
        if len(attachments) > AIBROKER_MM_MAX_FILES_TOTAL:
            return [], f"too many files (max {AIBROKER_MM_MAX_FILES_TOTAL})"

    global_files = list(request.FILES.getlist("files"))
    chunk_g, err_g = _upload_list(global_files)
    if err_g:
        return [], err_g
    attachments.extend(chunk_g)
    if len(attachments) > AIBROKER_MM_MAX_FILES_TOTAL:
        return [], f"too many files (max {AIBROKER_MM_MAX_FILES_TOTAL})"

    return attachments, None


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
