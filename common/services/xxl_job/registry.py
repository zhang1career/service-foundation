from __future__ import annotations

from collections.abc import Callable, Sequence

XxlHandler = Callable[[str | None], tuple[bool, str]]


class XxlJobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, XxlHandler] = {}

    def register(self, name: str, fn: XxlHandler) -> None:
        key = (name or "").strip()
        if not key:
            raise ValueError("handler name must be non-empty")
        self._jobs[key] = fn

    def get(self, name: str) -> XxlHandler | None:
        return self._jobs.get((name or "").strip())


_registry: XxlJobRegistry | None = None


def get_registry() -> XxlJobRegistry:
    global _registry
    if _registry is None:
        _registry = XxlJobRegistry()
    return _registry


def reset_registry_for_tests() -> None:
    global _registry
    _registry = None
