import base64
import binascii
import imghdr
import logging
import uuid
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import quote

from django.conf import settings

from common.exceptions import InvalidArgumentError, ObjectStorageError
from common.services.http import HttpCallError, request_sync

logger = logging.getLogger(__name__)


def _guess_ext(content_type: str, filename: str, data: bytes) -> str:
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    if content_type:
        mapping = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/webp": "webp",
        }
        if content_type.lower() in mapping:
            return mapping[content_type.lower()]
    kind = imghdr.what(None, h=data)
    return kind or "bin"


def _decode_data_url(value: str) -> Optional[Tuple[bytes, str]]:
    if not value.startswith("data:") or ";base64," not in value:
        return None
    header, encoded = value.split(",", 1)
    mime = header[5:].split(";")[0].strip().lower()
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise InvalidArgumentError("invalid avatar data url")
    return data, mime or "application/octet-stream"


def _decode_base64(value: str) -> Optional[bytes]:
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        return None


def _download_remote(url: str) -> Tuple[bytes, str, str]:
    try:
        resp = request_sync(
            method="GET",
            url=url,
            pool_name="avatar_http_pool",
            timeout_sec=10,
        )
    except HttpCallError as e:
        raise ObjectStorageError(f"failed to fetch avatar url: {e}") from e
    if resp.status_code != 200:
        raise InvalidArgumentError("failed to fetch avatar url")
    content_type = resp.headers.get("Content-Type", "application/octet-stream").split(";")[0].strip().lower()
    filename = url.split("?")[0].rsplit("/", 1)[-1]
    return resp.content, content_type, filename


def _http_put_object(*, url: str, data: bytes, content_type: str, timeout: int):
    headers = {"Content-Type": content_type}
    return request_sync(
        method="PUT",
        url=url,
        pool_name="avatar_http_pool",
        data=data,
        headers=headers,
        timeout_sec=timeout,
    )


def _oss_base_url() -> str:
    raw = getattr(settings, "USER_OSS_ENDPOINT", None)
    if raw is None or not str(raw).strip():
        return "http://127.0.0.1:8000/api/oss"
    return str(raw).strip().rstrip("/")


def _oss_bucket_name() -> str:
    raw = getattr(settings, "USER_OSS_BUCKET", None)
    if raw is None or not str(raw).strip():
        return "user-avatar"
    return str(raw).strip()


def upload_avatar(avatar) -> str:
    if avatar is None:
        return ""

    base = _oss_base_url()
    bucket = _oss_bucket_name()

    content_type = "application/octet-stream"
    filename = ""

    if hasattr(avatar, "read"):
        data = avatar.read()
        content_type = getattr(avatar, "content_type", "") or content_type
        filename = getattr(avatar, "name", "") or ""
    elif isinstance(avatar, str):
        value = avatar.strip()
        if not value:
            return ""
        decoded_data_url = _decode_data_url(value)
        if decoded_data_url:
            data, content_type = decoded_data_url
        elif value.startswith("http://") or value.startswith("https://"):
            data, content_type, filename = _download_remote(value)
        else:
            decoded = _decode_base64(value)
            if decoded is None:
                raise InvalidArgumentError("avatar must be file, base64, data url, or http url")
            data = decoded
            content_type = "application/octet-stream"
    else:
        raise InvalidArgumentError("unsupported avatar type")

    if not data:
        raise InvalidArgumentError("avatar is empty")

    ext = _guess_ext(content_type=content_type, filename=filename, data=data)
    object_key = f"avatar/{datetime.utcnow().strftime('%Y%m%d')}/{uuid.uuid4().hex}.{ext}"
    object_path = f"/api/oss/{bucket}/{quote(object_key, safe='/')}"
    public_url = object_path
    upload_url = f"{base}/{bucket}/{quote(object_key, safe='/')}"

    logger.info(
        "avatar OSS upload via HTTP PUT: base=%s bucket=%s key=%s bytes=%s content_type=%s",
        base,
        bucket,
        object_key,
        len(data),
        content_type,
    )

    try:
        put_resp = _http_put_object(url=upload_url, data=data, content_type=content_type, timeout=15)
    except HttpCallError as e:
        logger.exception("avatar HTTP PUT failed: %s", upload_url)
        raise ObjectStorageError(f"avatar upload request failed: {e}") from e
    except Exception as e:
        logger.exception("avatar HTTP PUT failed (unexpected): %s", upload_url)
        raise ObjectStorageError(f"avatar upload failed: {e}") from e

    if put_resp.status_code not in {200}:
        body_preview = (put_resp.text or "")[:500]
        logger.error(
            "avatar OSS rejected PUT: status=%s url=%s body_preview=%r",
            put_resp.status_code,
            upload_url,
            body_preview,
        )
        raise ObjectStorageError(
            f"failed to upload avatar to oss (HTTP {put_resp.status_code})",
        )

    logger.info("avatar OSS upload ok: public_url=%s", public_url)
    return public_url
