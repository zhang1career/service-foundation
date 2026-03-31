"""Limits and MIME allowlist for AI Broker multimodal uploads (console + text API)."""

from common.enums.content_type_enum import ContentTypeEnum

# Allowed multimodal MIME domain in enum form first.
AIBROKER_MM_ALLOWED_CONTENT_TYPES = frozenset(
    {
        ContentTypeEnum.IMAGE_JPEG,
        ContentTypeEnum.IMAGE_PNG,
        ContentTypeEnum.IMAGE_GIF,
        ContentTypeEnum.IMAGE_WEBP,
        ContentTypeEnum.AUDIO_MPEG,
        ContentTypeEnum.AUDIO_WAV,
        ContentTypeEnum.AUDIO_WEBM,
        ContentTypeEnum.AUDIO_OGG,
        ContentTypeEnum.APPLICATION_PDF,
        ContentTypeEnum.TEXT_PLAIN,
    }
)

# Extra aliases not currently covered by ContentTypeEnum.
_AIBROKER_MM_ALLOWED_MIME_ALIASES = frozenset({"audio/x-wav", "audio/flac"})

# Exact MIME types allowed for multipart uploads (browser-reported type must match).
AIBROKER_MM_ALLOWED_MIMES = frozenset(
    {content_type.to_mime_type() for content_type in AIBROKER_MM_ALLOWED_CONTENT_TYPES}
    | _AIBROKER_MM_ALLOWED_MIME_ALIASES
)

VARIABLE_KIND_TEXT = "text"
VARIABLE_KIND_IMAGE = "image"
VARIABLE_KIND_AUDIO = "audio"
VARIABLE_KIND_FILE = "file"

VARIABLE_KINDS_MEDIA = frozenset(
    {VARIABLE_KIND_IMAGE, VARIABLE_KIND_AUDIO, VARIABLE_KIND_FILE}
)
