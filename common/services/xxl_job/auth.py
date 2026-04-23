from __future__ import annotations

from typing import Any


def read_access_token(request: Any) -> str | None:
    t = (request.headers.get("Xxl-Job-Access-Token") or "").strip()
    if t:
        return t
    t = (getattr(request, "META", {}).get("HTTP_XXL_JOB_ACCESS_TOKEN") or "").strip()
    return t or None


def validate_token(*, provided: str | None, expected: str) -> bool:
    return bool(expected) and provided is not None and provided == expected
