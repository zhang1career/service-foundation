"""Replace ``://{{service_key}}`` using a resolver (Paganini ServiceUrlSpecifier-compatible)."""

from __future__ import annotations

import re
from collections.abc import Callable

# Same pattern as Paganini\ServiceDiscovery\ServiceUrlSpecifier::PATTERN
_SERVICE_HOST_IN_URL = re.compile(r"://\{\{([a-zA-Z0-9_-]*)\}\}")


def specify_service_host(
        url: str,
        resolve: Callable[[str, int | None], str],
        index: int | None = None,
) -> str:
    if not url:
        return ""
    match = _SERVICE_HOST_IN_URL.search(url)
    if not match:
        return url
    key = match.group(1)
    host = resolve(key, index)
    return url.replace("{{" + key + "}}", host)
