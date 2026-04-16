"""Validate config_entry.condition against condition_meta (field_key) for the same rid."""

from __future__ import annotations

import json
from typing import Any

from app_config.repos import condition_field_repo


def normalize_and_validate_condition(rid: int, condition_raw: str) -> str:
    """
    Parse condition as JSON object; keys must be a subset of condition_meta.field_key for rid.

    Returns canonical JSON string (sorted keys), or empty string when the object
    has no keys. Raises ValueError on invalid input or unknown keys.
    """
    s = (condition_raw or "").strip()
    if not s:
        obj: dict[str, Any] = {}
    else:
        try:
            obj = json.loads(s)
        except json.JSONDecodeError as exc:
            raise ValueError(f"condition must be valid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError("condition must be a JSON object")

    allowed = {row.field_key for row in condition_field_repo.list_fields_for_rid(rid)}
    keys_in_condition = set(obj.keys())
    extra = keys_in_condition - allowed
    if extra:
        raise ValueError(
            "condition contains keys not declared in condition_meta for this caller: "
            f"{sorted(extra)}; allowed: {sorted(allowed)}"
        )

    if not obj:
        return ""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
