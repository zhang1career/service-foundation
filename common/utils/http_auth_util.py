"""HTTP auth helpers: inbound header parsing and outbound JSON client request headers."""
from __future__ import annotations


def build_auth_headers(*, api_key: str = "", auth_mode: str = "bearer") -> dict[str, str]:
    """
    Build headers for outbound HTTP calls: ``application/json`` content type/accept plus optional auth.

    ``auth_mode``: ``bearer`` (default), ``api-key`` (header ``api-key``), or
    ``opensearch`` (``Authorization: ApiKey …``).
    """
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    key = str(api_key or "").strip()
    if not key:
        return headers
    if auth_mode == "api-key":
        headers["api-key"] = key
    elif auth_mode == "opensearch":
        headers["Authorization"] = f"ApiKey {key}"
    else:
        headers["Authorization"] = f"Bearer {key}"
    return headers


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
