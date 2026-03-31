"""Read ai_model.param_specs tree nodes (stored JSON keys: n, d, t, r, c, x)."""

from __future__ import annotations

from typing import Any, Optional

from common.enums.nested_type_enum import NestedParamType


def wire_param_name(node: dict[str, Any]) -> Optional[str]:
    v = node.get("n")
    return v.strip() if isinstance(v, str) else None


def wire_param_description(node: dict[str, Any]) -> str:
    v = node.get("d")
    return v if isinstance(v, str) else ""


def wire_param_type(node: dict[str, Any]) -> str:
    v = node.get("t")
    s = str(v).strip().upper() if v is not None else ""
    if not s:
        return NestedParamType.STRING.value
    # Legacy wire value removed from enum; treat as STRING.
    if s == "TEXT":
        return NestedParamType.STRING.value
    return s


def wire_param_range(node: dict[str, Any]) -> dict[str, Any]:
    v = node.get("r")
    return v if isinstance(v, dict) else {}


def wire_param_children(node: dict[str, Any]) -> list[Any]:
    v = node.get("c")
    return v if isinstance(v, list) else []


def wire_param_placeholder(node: dict[str, Any]) -> str:
    """Must match a top-level model_params key; ``content`` is the rendered user message."""
    v = node.get("x")
    return v.strip() if isinstance(v, str) else ""
