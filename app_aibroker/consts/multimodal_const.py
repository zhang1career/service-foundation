"""Limits and MIME allowlist for AI Broker multimodal uploads (console + text API)."""

AIBROKER_MM_MAX_FILES_TOTAL = 16
AIBROKER_MM_MAX_BYTES_PER_FILE = 20 * 1024 * 1024

# Exact MIME types allowed for multipart uploads (browser-reported type must match).
AIBROKER_MM_ALLOWED_MIMES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
        "audio/flac",
        "application/pdf",
        "text/plain",
    }
)

VARIABLE_KIND_TEXT = "text"
VARIABLE_KIND_IMAGE = "image"
VARIABLE_KIND_AUDIO = "audio"
VARIABLE_KIND_FILE = "file"

VARIABLE_KINDS_MEDIA = frozenset(
    {VARIABLE_KIND_IMAGE, VARIABLE_KIND_AUDIO, VARIABLE_KIND_FILE}
)
