from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError

from app_cms.models.content_meta import CMS_DYNAMIC_TABLE_PREFIX, CmsContentMeta
from app_cms.schema.content_meta_fields import (
    SCHEMA_VERSION,
    normalize_fields_document,
    validate_fields_document,
)

_META_NAME_BODY_MAX = 63 - len(CMS_DYNAMIC_TABLE_PREFIX) - 1
META_NAME_RE = re.compile(rf"^[a-z][a-z0-9_]{{0,{_META_NAME_BODY_MAX}}}$")

_COL_PAT = re.compile(r"^fields\[columns\]\[(\d+)\]\[(\w+)\]$")
_VAL_PAT = re.compile(r"^fields\[columns\]\[(\d+)\]\[validation\]\[(\w+)\]$")
_IDX_COL_PAT = re.compile(r"^fields\[indexes\]\[(\d+)\]\[columns\]$")
_IDX_UNIQ_PAT = re.compile(r"^fields\[indexes\]\[(\d+)\]\[unique\]$")


def parse_content_meta_fields_from_post(post) -> dict[str, Any]:
    """Parse ``fields[columns][i][…]`` and ``fields[indexes][i][…]`` from a ``QueryDict``."""
    col_buckets: dict[int, dict[str, Any]] = {}
    for key in post.keys():
        m = _COL_PAT.match(key)
        if m:
            idx = int(m.group(1))
            field = m.group(2)
            if field == "validation":
                continue
            col_buckets.setdefault(idx, {})[field] = post.get(key)
        m = _VAL_PAT.match(key)
        if m:
            idx = int(m.group(1))
            sub = m.group(2)
            col_buckets.setdefault(idx, {}).setdefault("validation", {})[sub] = post.get(key)

    columns: list[dict[str, Any]] = []
    for i in sorted(col_buckets.keys()):
        row = col_buckets[i]
        name = (row.get("name") or "").strip()
        if not name:
            continue
        columns.append(_normalize_column_from_post(row))

    indexes: list[dict[str, Any]] = []
    idx_cols: dict[int, str] = {}
    idx_uniq: dict[int, bool] = {}
    for key in post.keys():
        m = _IDX_COL_PAT.match(key)
        if m:
            idx_cols[int(m.group(1))] = str(post.get(key) or "")
        m = _IDX_UNIQ_PAT.match(key)
        if m:
            idx_uniq[int(m.group(1))] = _as_bool(post.get(key))

    for i in sorted(set(idx_cols.keys()) | set(idx_uniq.keys())):
        raw = idx_cols.get(i, "")
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            continue
        indexes.append({"columns": parts, "unique": idx_uniq.get(i, False)})

    return {"schema_version": SCHEMA_VERSION, "columns": columns, "indexes": indexes}


def _parse_column_index_from_post(row: dict[str, Any]) -> str:
    raw = row.get("index")
    if raw is not None and raw != "":
        s = str(raw).strip().lower()
        if s in ("none", "无"):
            return "none"
        if s == "key":
            return "key"
        if s == "unique":
            return "unique"
        return "none"
    if _as_bool(row.get("unique")):
        return "unique"
    return "none"


def _normalize_column_from_post(row: dict[str, Any]) -> dict[str, Any]:
    col: dict[str, Any] = {
        "name": str(row.get("name") or "").strip(),
        "physical": str(row.get("physical") or "").strip(),
        "nullable": _as_bool(row.get("nullable")),
        "index": _parse_column_index_from_post(row),
    }
    comment_raw = row.get("comment")
    if comment_raw is not None:
        col["comment"] = str(comment_raw).strip()
    vraw = row.get("validation")
    if isinstance(vraw, dict):
        vb: dict[str, Any] = {}
        t = str(vraw.get("type") or "").strip()
        if t:
            vb["type"] = t
        if "required" in vraw:
            vb["required"] = _as_bool(vraw.get("required"))
        if vb.get("type"):
            col["validation"] = vb
    return col


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v in (None, "", "0", 0):
        return False
    if v in ("1", 1, "true", "on", "yes"):
        return True
    return bool(v)


def validate_store_meta(*, name: str, fields: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(name, str) or not META_NAME_RE.match(name):
        raise ValidationError({"name": "Invalid name format"})
    if CmsContentMeta.objects.filter(name=name).exists():
        raise ValidationError({"name": "This name is already taken"})
    normalized = normalize_fields_document(fields)
    validate_fields_document(normalized)
    return {"name": name, "fields": normalized}


def validate_update_meta(*, fields: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_fields_document(fields)
    validate_fields_document(normalized)
    return {"fields": normalized}
