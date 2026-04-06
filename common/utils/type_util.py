"""Coercion helpers for primitive types (HTTP/JSON payloads)."""
from __future__ import annotations

from typing import Any


def parse_int_or_default(raw: Any, default: int) -> int:
    """
    Parse *raw* as int; ``None`` or blank string → *default*.
    If *raw* is present but not parseable as int, raises ``ValueError("invalid integer")``.
    """
    if raw is None:
        return default
    if isinstance(raw, str) and not raw.strip():
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValueError("invalid integer")
