"""Condition filtering and shallow merge of config_entry rows (ut ascending)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from common.utils.dict_util import merge

from app_config.enums import ConfigEntryPublic
from app_config.models import ConfigEntry
from app_config.repos import config_entry_repo


def canonical_conditions_json(conditions: dict[str, Any]) -> str:
    return json.dumps(conditions, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def conditions_hash(conditions: dict[str, Any]) -> str:
    raw = canonical_conditions_json(conditions).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def normalize_conditions(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("conditions must be a JSON object")
    return raw


def _parse_row_condition(condition_str: str) -> dict[str, Any] | None:
    try:
        o = json.loads(condition_str or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(o, dict):
        return None
    return o


def _row_matches(cond: dict[str, Any], request_conditions: dict[str, Any]) -> bool:
    for k, v in cond.items():
        if k not in request_conditions:
            return False
        if request_conditions[k] != v:
            return False
    return True


def _layer_audit(
    row: ConfigEntry,
    cond: dict[str, Any],
    request_conditions: dict[str, Any],
) -> dict[str, Any]:
    keys = sorted(cond.keys())
    satisfied = {k: request_conditions[k] for k in cond if k in request_conditions}
    return {
        "config_id": row.id,
        "row_condition": cond,
        "condition_keys": keys,
        "satisfied_by_request": satisfied,
    }


def merge_config_query_result(
    rid: int,
    config_key: str,
    conditions: dict[str, Any],
    *,
    endpoint_mode: str,
) -> dict[str, Any]:
    """
    Return API data payload: ``value``, ``_ids``; ``_explain`` only when
    ``endpoint_mode`` is ``pri`` (omitted for ``pub``).

    ``config_entry.public`` (``ConfigEntryPublic``): **public=1** 不按 ``condition`` 过滤；
    **private=0** 按 ``condition`` 与请求 ``conditions`` 子集匹配。

    ``endpoint_mode``:
    - ``pub``: only ``public=1`` rows (no login API).
    - ``pri``: ``public=1`` and ``public=0`` rows.

    Shallow merge: for each matching row in ut ascending, merge dicts with ``common.utils.dict_util.merge``.
    If a row's parsed value is not a dict, it becomes the whole merged value and merging stops.
    """
    if endpoint_mode not in ("pub", "pri"):
        raise ValueError("endpoint_mode must be pub or pri")

    rows = config_entry_repo.list_entries_for_rid_and_key(rid, config_key)
    matched: list[ConfigEntry] = []
    for row in rows:
        is_public_row = int(row.public) == ConfigEntryPublic.PUBLIC
        if endpoint_mode == "pub" and not is_public_row:
            continue
        if is_public_row:
            matched.append(row)
            continue
        cond = _parse_row_condition(row.condition)
        if cond is None:
            continue
        if not _row_matches(cond, conditions):
            continue
        matched.append(row)

    matched.sort(key=lambda r: (r.ut, r.id))

    merged: Any | None = None
    source_ids: list[int] = []
    matched_layers: list[dict[str, Any]] = []

    for row in matched:
        if int(row.public) == ConfigEntryPublic.PUBLIC:
            cond: dict[str, Any] = {}
        else:
            cond = _parse_row_condition(row.condition) or {}
        try:
            parsed = json.loads(row.value)
        except json.JSONDecodeError:
            continue
        source_ids.append(row.id)
        matched_layers.append(_layer_audit(row, cond, conditions))

        if merged is None:
            merged = parsed
        elif isinstance(merged, dict) and isinstance(parsed, dict):
            merged = merge(merged, parsed)
        else:
            merged = parsed
            break

    source_ids_str = ",".join(str(i) for i in source_ids)

    out: dict[str, Any] = {
        "value": merged,
        "_ids": source_ids_str,
    }
    if endpoint_mode == "pri":
        out["_explain"] = {
            "conditions_received": dict(conditions),
            "matched_layers": matched_layers,
        }
    return out
