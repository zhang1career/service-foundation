"""
Registry for HTTP dict / enum metadata (k=display, v=stored id string).

Python uses decorators (similar in role to Java annotations) to register providers.
"""
from __future__ import annotations

import functools
import logging
from typing import Any, Dict, List, Type

logger = logging.getLogger(__name__)

_REGISTRY: Dict[str, Type[Any]] = {}
_BUNDLED_LOADED = False


def register_dict_code(code: str):
    """
    Decorator: register a class that defines classmethod to_dict_list() -> list[dict]
    with keys "k" (display) and "v" (submit value, typically str).
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        c = (code or "").strip()
        if not c:
            raise ValueError("dict code must be non-empty")
        method = getattr(cls, "to_dict_list", None)
        if method is None or not callable(method):
            raise TypeError(
                f"{cls.__name__} must define classmethod to_dict_list for dict code {c!r}"
            )
        existing = _REGISTRY.get(c)
        if existing is not None and existing is not cls:
            raise ValueError(
                f"duplicate dict code {c!r}: already registered as {existing.__name__}"
            )
        _REGISTRY[c] = cls
        return cls

    return decorator


def _ensure_bundled_common() -> None:
    global _BUNDLED_LOADED
    if _BUNDLED_LOADED:
        return
    try:
        import common.dict_catalog.bundled  # noqa: F401
    except Exception as e:
        logger.warning("[dict_catalog] bundled common dict codes failed: %s", e)
    _BUNDLED_LOADED = True


def _compute_dict_by_codes(codes: str) -> Dict[str, List[Dict[str, Any]]]:
    """Build dict response for one ``codes`` string (uncached)."""
    _ensure_bundled_common()
    if not codes or not isinstance(codes, str):
        return {}
    out: Dict[str, List[Dict[str, Any]]] = {}
    for raw in codes.split(","):
        c = raw.strip()
        if not c:
            continue
        cls = _REGISTRY.get(c)
        if cls is None:
            continue
        try:
            items = cls.to_dict_list()
        except Exception as e:
            logger.exception("[dict_catalog] to_dict_list failed for code=%s: %s", c, e)
            continue
        if not isinstance(items, list):
            continue
        out[c] = items
    return out


@functools.lru_cache(maxsize=256)
def get_dict_by_codes(codes: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Return { code: [ {"k", "v"}, ... ], ... } for known codes; omit unknown codes.

    Results are memoized per exact ``codes`` string (process-local). Call
    ``clear_dict_registry_for_tests`` in tests when the registry is reset.
    """
    return _compute_dict_by_codes(codes)


def warm_dict_catalog_bundled() -> None:
    """Import bundled dict registrations early to reduce first-request latency."""
    _ensure_bundled_common()


def dict_value_to_label(code: str, raw: Any) -> str:
    """Map a stored value to display label for code; fallback to str(raw)."""
    _ensure_bundled_common()
    c = (code or "").strip()
    if not c:
        return str(raw)
    cls = _REGISTRY.get(c)
    if cls is None:
        return str(raw)
    try:
        items = cls.to_dict_list()
    except Exception:
        return str(raw)
    if not isinstance(items, list):
        return str(raw)
    target = str(raw)
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("v")) == target:
            return str(item.get("k", raw))
    return str(raw)


def clear_dict_registry_for_tests() -> None:
    """Test helper: drop all registrations (including bundled)."""
    global _BUNDLED_LOADED
    get_dict_by_codes.cache_clear()
    _REGISTRY.clear()
    _BUNDLED_LOADED = False
