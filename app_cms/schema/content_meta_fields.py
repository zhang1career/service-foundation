"""Canonical shape of ``content_meta.fields`` — drives DDL, ORM, and API validation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from django.core.exceptions import ValidationError

SCHEMA_VERSION = 1

COLUMN_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")

# MySQL column types allowed in DDL (no raw SQL concatenation from untrusted input).
_PHYSICAL_RE = re.compile(
    r"^("
    r"char\([1-9][0-9]*\)|"
    r"varchar\([1-9][0-9]{0,4}\)|"
    r"text|longtext|"
    r"bigint unsigned|int unsigned|tinyint unsigned|"
    r"datetime\(6\)|datetime|"
    r"json"
    r")$"
)

# Appended automatically to every row table (not configurable in column definitions).
RESERVED_COLUMN_NAMES = frozenset({"id", "ct", "ut"})

# API validation kind for each user column (coercion / required semantics).
VALIDATION_TYPES = frozenset({"string", "text", "integer", "date", "json"})

# Per-column index intent (single-column indexes are merged into ``fields.indexes`` for DDL).
COLUMN_INDEX_KINDS = frozenset({"none", "key", "unique"})


def fields_document_hash(fields: dict[str, Any]) -> str:
    """Stable hash for dynamic model cache invalidation."""
    payload = json.dumps(fields.get("columns", []), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_fields_document(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical ``fields`` dict (schema_version, columns, indexes)."""
    if not isinstance(raw, dict):
        return {"schema_version": SCHEMA_VERSION, "columns": [], "indexes": []}
    columns = _normalize_columns(raw.get("columns"))
    for col in columns:
        if isinstance(col, dict):
            _migrate_legacy_column_index(col)
            _apply_inferred_column_default(col)
    indexes = _merge_indexes_from_columns(_normalize_indexes(raw.get("indexes")), columns)
    out: dict[str, Any] = {
        "schema_version": int(raw.get("schema_version") or SCHEMA_VERSION),
        "columns": columns,
        "indexes": indexes,
    }
    return out


def validate_fields_document(fields: dict[str, Any]) -> None:
    """Raise ``ValidationError`` if ``fields`` cannot define a table and validation rules."""
    if not isinstance(fields, dict):
        raise ValidationError({"fields": "fields must be a JSON object"})
    ver = int(fields.get("schema_version") or SCHEMA_VERSION)
    if ver != SCHEMA_VERSION:
        raise ValidationError({"fields": f"Unsupported schema_version (expected {SCHEMA_VERSION})"})

    columns = fields.get("columns")
    if not isinstance(columns, list) or len(columns) < 1:
        raise ValidationError({"fields": "fields.columns must be a non-empty array"})

    seen: set[str] = set()
    for i, col in enumerate(columns):
        if not isinstance(col, dict):
            raise ValidationError({f"fields.columns.{i}": "Each column must be an object"})
        _validate_one_column(i, col, seen)

    indexes = fields.get("indexes")
    if indexes is not None:
        if not isinstance(indexes, list):
            raise ValidationError({"fields.indexes": "Must be an array"})
        col_names = {c["name"] for c in columns if isinstance(c.get("name"), str)}
        for j, idx in enumerate(indexes):
            if not isinstance(idx, dict):
                raise ValidationError({f"fields.indexes.{j}": "Each index must be an object"})
            cols = idx.get("columns")
            if not isinstance(cols, list) or len(cols) < 1:
                raise ValidationError({f"fields.indexes.{j}.columns": "Must be a non-empty array"})
            for cn in cols:
                if cn not in col_names:
                    raise ValidationError(
                        {f"fields.indexes.{j}": f"Unknown column name in index: {cn}"}
                    )


def _validate_one_column(i: int, col: dict[str, Any], seen: set[str]) -> None:
    name = col.get("name")
    if not isinstance(name, str) or not COLUMN_NAME_RE.match(name):
        raise ValidationError({f"fields.columns.{i}.name": "Invalid column name"})
    if name in RESERVED_COLUMN_NAMES:
        raise ValidationError(
            {f"fields.columns.{i}.name": f"Reserved name {name!r} (system columns are added automatically)"}
        )
    if name in seen:
        raise ValidationError({f"fields.columns.{i}.name": f"Duplicate column {name!r}"})
    seen.add(name)

    physical = col.get("physical")
    if not isinstance(physical, str) or not _PHYSICAL_RE.match(physical.strip()):
        raise ValidationError({f"fields.columns.{i}.physical": "Unsupported or invalid physical type"})
    col["physical"] = physical.strip()

    if "nullable" not in col:
        col["nullable"] = True
    elif not isinstance(col["nullable"], bool):
        raise ValidationError({f"fields.columns.{i}.nullable": "Must be boolean"})

    _migrate_legacy_column_index(col)
    kind = col.get("index")
    if not isinstance(kind, str) or kind not in COLUMN_INDEX_KINDS:
        raise ValidationError({f"fields.columns.{i}.index": "Must be one of: none, key, unique"})

    if "comment" in col:
        cmt = col["comment"]
        if cmt is None:
            col.pop("comment", None)
        elif not isinstance(cmt, str):
            raise ValidationError({f"fields.columns.{i}.comment": "Must be a string"})
        else:
            s = cmt.strip()
            if len(s) > 1024:
                raise ValidationError(
                    {f"fields.columns.{i}.comment": "Must be at most 1024 characters"}
                )
            if s:
                col["comment"] = s
            else:
                col.pop("comment", None)

    v = col.get("validation")
    if v is None:
        raise ValidationError({f"fields.columns.{i}.validation": "Each column must include validation rules"})
    if not isinstance(v, dict):
        raise ValidationError({f"fields.columns.{i}.validation": "Must be an object"})
    _validate_validation_block(i, v)


def _validate_validation_block(i: int, v: dict[str, Any]) -> None:
    t = v.get("type")
    if t not in VALIDATION_TYPES:
        raise ValidationError({f"fields.columns.{i}.validation.type": "Invalid validation type"})
    if "required" in v and not isinstance(v["required"], bool):
        raise ValidationError({f"fields.columns.{i}.validation.required": "Must be boolean"})


def _normalize_columns(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(dict(item))
    return out


def _normalize_indexes(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        cols = item.get("columns")
        if isinstance(cols, list):
            out.append(
                {
                    "columns": [str(c) for c in cols if c is not None],
                    "unique": bool(item.get("unique")),
                }
            )
    return out


def _migrate_legacy_column_index(col: dict[str, Any]) -> None:
    """Set ``index`` from legacy ``unique`` boolean; drop ``unique``."""
    if isinstance(col.get("index"), str):
        s = col["index"].strip().lower()
        if s in COLUMN_INDEX_KINDS:
            col["index"] = s
        else:
            col["index"] = "none"
    elif _schema_bool(col, "unique", default=False):
        col["index"] = "unique"
    else:
        col["index"] = "none"
    col.pop("unique", None)


def _physical_allows_empty_string_default(physical_lower: str) -> bool:
    """Only char/varchar may use ``DEFAULT ''``; TEXT/LONGTEXT/BLOB/JSON cannot in MySQL."""
    return bool(
        re.match(r"^char\([1-9][0-9]*\)$", physical_lower)
        or re.match(r"^varchar\([1-9][0-9]{0,4}\)$", physical_lower)
    )


def _physical_is_integer_type(physical_lower: str) -> bool:
    return physical_lower in ("int unsigned", "bigint unsigned", "tinyint unsigned")


def _apply_inferred_column_default(col: dict[str, Any]) -> None:
    """For NOT NULL string/int columns, set implicit SQL defaults when unset."""
    if "default" in col:
        return
    physical = (col.get("physical") or "").strip().lower()
    if not physical:
        return
    if column_allows_sql_null(col):
        return
    if _physical_allows_empty_string_default(physical):
        col["default"] = ""
    elif _physical_is_integer_type(physical):
        col["default"] = 0


def _merge_indexes_from_columns(
    explicit: list[dict[str, Any]], columns: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Append single-column indexes from ``columns[].index``; dedupe by (columns, unique)."""
    sig_seen: set[tuple[bool, tuple[str, ...]]] = set()
    out: list[dict[str, Any]] = []
    for idx in explicit:
        cols = idx.get("columns") or []
        if not cols:
            continue
        sig = (bool(idx.get("unique")), tuple(cols))
        if sig in sig_seen:
            continue
        sig_seen.add(sig)
        out.append(dict(idx))

    for col in columns:
        if not isinstance(col, dict):
            continue
        name = col.get("name")
        if not isinstance(name, str) or not name:
            continue
        kind = column_index_kind(col)
        if kind == "key":
            sig = (False, (name,))
        elif kind == "unique":
            sig = (True, (name,))
        else:
            continue
        if sig in sig_seen:
            continue
        sig_seen.add(sig)
        out.append({"columns": [name], "unique": sig[0]})
    return out


def reserved_row_column_sql() -> list[str]:
    """DDL fragments for ``ct`` / ``ut`` (after user columns, before PRIMARY KEY)."""
    return [
        "`ct` bigint unsigned NOT NULL DEFAULT 0 COMMENT 'Create time in Unix milliseconds'",
        "`ut` bigint unsigned NOT NULL DEFAULT 0 COMMENT 'Update time in Unix milliseconds'",
    ]


def _schema_bool(col: dict[str, Any], key: str, *, default: bool) -> bool:
    if key not in col:
        return default
    v = col[key]
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("0", "false", "no", "off", ""):
            return False
        if s in ("1", "true", "yes", "on"):
            return True
    return bool(v)


def column_allows_sql_null(col: dict[str, Any]) -> bool:
    return _schema_bool(col, "nullable", default=True)


def column_index_kind(col: dict[str, Any]) -> str:
    """``none`` | ``key`` | ``unique`` (single-column intent; ``key``/``unique`` are realized via ``indexes``)."""
    v = col.get("index")
    if isinstance(v, str) and v in COLUMN_INDEX_KINDS:
        return v
    if _schema_bool(col, "unique", default=False):
        return "unique"
    return "none"


def column_is_unique(col: dict[str, Any]) -> bool:
    """ORM unique flag for CharField; matches ``index == \"unique\"``."""
    return column_index_kind(col) == "unique"


def infer_sql_default(col: dict[str, Any]) -> Any | None:
    """Effective default for DDL when ``default`` key is absent."""
    if "default" in col:
        return col.get("default")
    physical = (col.get("physical") or "").strip().lower()
    if not physical:
        return None
    if column_allows_sql_null(col):
        return None
    if _physical_allows_empty_string_default(physical):
        return ""
    if _physical_is_integer_type(physical):
        return 0
    return None


def _mysql_column_comment_clause(col: dict[str, Any]) -> str:
    """Return `` COMMENT '…'`` for DDL, or empty string if absent/blank."""
    raw = col.get("comment")
    if not isinstance(raw, str):
        return ""
    s = raw.strip()
    if not s:
        return ""
    if len(s) > 1024:
        s = s[:1024]
    escaped = s.replace("\\", "\\\\").replace("'", "''")
    return f" COMMENT '{escaped}'"


def ddl_column_definition_tail(col: dict[str, Any]) -> str:
    name = col.get("name") or "?"
    parts: list[str] = [col["physical"]]
    if not column_allows_sql_null(col):
        parts.append("NOT NULL")
    default = infer_sql_default(col)
    if default is not None:
        if isinstance(default, bool):
            parts.append("DEFAULT 1" if default else "DEFAULT 0")
        elif isinstance(default, int):
            parts.append(f"DEFAULT {int(default)}")
        elif isinstance(default, str):
            if default.upper() == "CURRENT_TIMESTAMP":
                parts.append("DEFAULT CURRENT_TIMESTAMP(6)")
            else:
                escaped = default.replace("\\", "\\\\").replace("'", "''")
                parts.append(f"DEFAULT '{escaped}'")
        else:
            raise ValueError(f"Unsupported default for {name!r}")
    tail = " ".join(parts)
    return tail + _mysql_column_comment_clause(col)


def ddl_column_definition(col: dict[str, Any]) -> str:
    name = col["name"]
    return f"`{name}` {ddl_column_definition_tail(col)}"


def index_definition_sql(table: str, index: dict[str, Any], ordinal: int) -> str:
    cols = index.get("columns") or []
    col_sql = ", ".join(f"`{c}`" for c in cols)
    unique = "UNIQUE " if index.get("unique") else ""
    iname = _short_identifier(f"{table}_idx_{ordinal}", 60)
    return f"{unique}KEY `{iname}` ({col_sql})"


def _short_identifier(name: str, max_len: int) -> str:
    if len(name) <= max_len:
        return name
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:12]
    return f"{name[: max_len - 13]}_{digest}"


def column_accessors(columns: list[dict[str, Any]]) -> dict[str, str]:
    """Map DB column name → Django attribute name (identity for user columns)."""
    return {col["name"]: col["name"] for col in columns if isinstance(col.get("name"), str)}
