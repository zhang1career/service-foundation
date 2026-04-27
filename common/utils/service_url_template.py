"""
Fusio-style ``://{{service_key}}`` URL helpers (Paganini ``ServiceUrlSpecifier`` shape).

Production code resolves placeholders via Redis — see
``common.services.service_discovery.expand_service_discovery_url`` (mall-agg /
``RedisServiceUriResolver``).

:func:`expand_service_url_from_env` remains for **tests and local tooling** only: it replaces
``{{service_key}}`` using ``SERVICE_HOST_<KEY>`` (``-`` → ``_``, uppercased).

:func:`substitute_url_context_placeholders` mirrors Fusio ``ArgumentHelper::specifyPath`` for
remaining ``{{name}}`` segments using a caller-supplied mapping (e.g. saga ``idem_key``).

**Convention:** the token immediately after ``://{{`` is always a **service registry key** (host
placeholders), not a path/context key. Path/context values belong in other ``{{name}}`` segments
after the host, e.g. ``http://{{order-svc}}/api/sagas/{{idem_key}}/action``.

Call :func:`ensure_url_has_no_unresolved_placeholders` after host + context substitution
before HTTP, so unresolved or malformed ``{{...}}`` never leaves the process as a request URL.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping

# paganini ServiceUrlSpecifier: first ://{{key}} only; key charset matches PHP.
_SERVICE_HOST_IN_URL = re.compile(r"://\{\{([a-zA-Z0-9_-]*)\}\}")

# Fusio ArgumentHelper::specifyPath-compatible ``{{name}}`` keys (path / query segments).
_CONTEXT_PLACEHOLDER_IN_URL = re.compile(r"\{\{([a-zA-Z0-9_-]*)\}\}")


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

    *service_key* must be a service-registry name (Paganini / Redis), not a path or context
    variable; use a separate ``{{name}}`` after the host for path template values.

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


def substitute_url_context_placeholders(
    url: str,
    variables: Mapping[str, str] | None,
) -> str:
    """
    Replace ``{{name}}`` segments when *name* is a key in *variables* (Fusio-style path args).

    Unknown placeholders are left unchanged; callers that forbid stale templates should call
    :func:`ensure_url_has_no_unresolved_placeholders` after this step. Run after
    :func:`specify_service_host` / service-discovery expansion.
    """
    if not url or not variables:
        return url or ""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables:
            return variables[key]
        return match.group(0)

    return _CONTEXT_PLACEHOLDER_IN_URL.sub(_replace, url)


def ensure_url_has_no_unresolved_placeholders(url: str) -> None:
    """
    Require that *url* contains no ``{{name}}`` placeholders (name: ``[a-zA-Z0-9_-]*``) and no
    stray ``{{`` after template processing. Raises :class:`ServiceUrlResolutionError` otherwise.
    """
    if not url or "{{" not in url:
        return
    m = _CONTEXT_PLACEHOLDER_IN_URL.search(url)
    if m is not None:
        name = m.group(1) or "?"
        token = "{{" + name + "}}"
        raise ServiceUrlResolutionError(
            f"Unresolved URL placeholder {token!r}; add it to the template context or fix the URL"
        )
    raise ServiceUrlResolutionError(
        "Invalid or incomplete {{...}} in URL (use {{name}} with characters [a-zA-Z0-9_-] only)"
    )


def expand_service_url_from_env(url: str, index: int | None = None) -> str:
    """Convenience: ``specify_service_host`` with :func:`resolve_service_host_from_env`."""
    return specify_service_host(url, resolve_service_host_from_env, index)
