"""AiModel.capability values (DB smallint)."""
from enum import IntEnum


class ModelCapabilityEnum(IntEnum):
    """0 chat, 1 image, 2 video, 3 embedding — matches ai_model field comment."""

    CHAT = 0
    IMAGE = 1
    VIDEO = 2
    EMBEDDING = 3
