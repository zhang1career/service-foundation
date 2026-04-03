"""HTTP Authorization header helpers (framework-agnostic string / request META)."""
from __future__ import annotations


def authorization_header_from_request(request) -> str:
    """Return the raw ``Authorization`` header value, or empty string if absent."""
    raw = request.META.get("HTTP_AUTHORIZATION", "")
    return raw if isinstance(raw, str) else ""


def parse_bearer_token(auth_header: str | None) -> str | None:
    """Parse a ``Bearer`` token from an ``Authorization`` header value. Return ``None`` if invalid."""
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()
