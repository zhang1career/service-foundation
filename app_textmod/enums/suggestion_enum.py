from __future__ import annotations

from enum import IntEnum


class TextmodSuggestionEnum(IntEnum):
    """Per-hit moderation suggestion (numeric id for dict + storage)."""

    PASS = 0
    REVIEW = 1
    BLOCK = 2

    @classmethod
    def to_api(cls, value: int) -> str:
        if value == cls.BLOCK:
            return "block"
        if value == cls.REVIEW:
            return "review"
        return "pass"
