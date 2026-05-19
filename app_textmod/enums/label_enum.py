from __future__ import annotations

from enum import IntEnum


class TextmodLabelEnum(IntEnum):
    """Baseline labels for dict discovery; callers may use custom positive ints."""

    NORMAL = 0
    CUSTOM = 1
    PROFANITY = 2
    PORN = 3
    ILLEGAL = 4
    POLITICAL = 5
    AD = 6
    SPAM = 7
