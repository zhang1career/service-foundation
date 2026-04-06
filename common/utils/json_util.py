from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def json_encode(result):
    return json.dumps(result, indent=None, default=str)


def json_decode(param: str | None) -> Any:
    """
    Parse a JSON document from *param* (UTF-8 text). ``None`` → ``None``.

    Raises:
        TypeError: *param* is not ``None`` and not a ``str``.
        ValueError: empty / whitespace-only string, or invalid JSON.
    """
    if param is None:
        return None
    if not isinstance(param, str):
        raise TypeError("json_decode expects str or None")
    s = param.strip()
    if not s:
        raise ValueError("json_decode: empty or whitespace-only string")
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"json_decode: invalid JSON: {e}") from e


def json_decode_from_bytes(raw: bytes | None) -> dict | list | None:
    """
    Decode UTF-8 *raw* to text, then :func:`json_decode`.

    Returns a ``dict`` or ``list`` when the JSON top-level value is an object or array.
    Returns ``None`` when decoding fails, UTF-8 is invalid, or the top-level value is
    not an object or array (e.g. string, number, boolean, ``null``).
    """
    if raw is None:
        return None
    if not isinstance(raw, bytes):
        raise TypeError("json_decode_from_bytes expects bytes or None")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        data = json_decode(text)
    except ValueError as exc:
        logger.warning("json_decode_from_bytes: json_decode failed: %s", exc, exc_info=True)
        return None
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return data
    return None
