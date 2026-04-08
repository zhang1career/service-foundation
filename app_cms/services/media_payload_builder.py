from __future__ import annotations

from typing import Any

from app_cms.models.media_file import CmsMediaFile


def media_payload_from_model(media: CmsMediaFile | None) -> dict[str, Any] | None:
    if media is None:
        return None
    return {
        "id": media.pk,
        "cdn_url": media.cdn_url,
        "ready": media.is_ready(),
        "mime_type": media.mime_type,
    }
