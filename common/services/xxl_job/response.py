"""XXL-JOB executor HTTP JSON shape (``code`` / ``msg`` / ``data``)."""

from __future__ import annotations

from typing import Any


def success(data: Any = None, msg: str = "") -> dict[str, Any]:
    return {"data": data, "code": 200, "msg": msg}


def fail(message: str) -> dict[str, Any]:
    return {"data": None, "code": 500, "msg": message}
