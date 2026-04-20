"""
Resolve Fusio-style service placeholders in URLs (compatible with paganini ``ServiceUrlSpecifier``).

If a value contains ``://{{service_key}}``, the first such occurrence is resolved by replacing
all ``{{service_key}}`` segments in the string with a host value from the environment.

Default lookup: ``SERVICE_HOST_<KEY>`` where ``<KEY>`` is ``service_key`` with ``-`` replaced by
``_`` and uppercased (e.g. ``sf-snowflake`` -> ``SERVICE_HOST_SF_SNOWFLAKE``).
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable

# paganini ServiceUrlSpecifier: first ://{{key}} only; key charset matches PHP.
_SERVICE_HOST_IN_URL = re.compile(r"://\{\{([a-zA-Z0-9_-]*)\}\}")


class ServiceUrlResolutionError(RuntimeError):
    """Raised when a ``{{service_key}}`` segment cannot be resolved."""


def _service_host_env_name(service_key: str) -> str:
    return f"SERVICE_HOST_{service_key.replace('-', '_').upper()}"


def resolve_service_host_from_env(service_key: str, index: int | None = None) -> str:
    """
    Read ``host[:port]`` for ``service_key`` from ``SERVICE_HOST_<KEY>``.

    ``index`` is accepted for API parity with multi-instance resolvers; the env backend ignores it.
    """
    _ = index
    name = _service_host_env_name(service_key)
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        raise ServiceUrlResolutionError(
            f"Cannot resolve {{{{{service_key}}}}}: set {name} or use a URL without service placeholders"
        )
    return raw


def specify_service_host(
    url: str,
    resolve: Callable[[str, int | None], str],
    index: int | None = None,
) -> str:
    """
    Replace ``{{service_key}}`` in ``url`` when the URL contains ``://{{service_key}}``.

    Mirrors ``Paganini\\ServiceDiscovery\\ServiceUrlSpecifier::specifyHost``:
    only the first ``://{{...}}`` match selects the key; then every ``{{key}}`` in ``url`` is
    replaced with the resolved host (typically ``host:port``).
    """
    if not url:
        return ""
    if "://{{" not in url:
        return url
    match = _SERVICE_HOST_IN_URL.search(url)
    if not match:
        return url
    key = match.group(1)
    host = resolve(key, index)
    return url.replace("{{" + key + "}}", host)


def expand_service_url_from_env(url: str, index: int | None = None) -> str:
    """Convenience: ``specify_service_host`` with :func:`resolve_service_host_from_env`."""
    return specify_service_host(url, resolve_service_host_from_env, index)
