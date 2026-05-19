"""Parse lexicon bulk-import files (UTF-8 .txt / .csv).

Cloud consoles commonly accept:
- newline-delimited keywords in a text file (e.g. Tencent 文本内容安全批量导入说明);
- CSV with one keyword per row, often with a template header (e.g. Alibaba content-moderation libraries).

This module accepts:
- ``.txt``: one term per line; empty lines and ``#`` comments skipped; UTF-8 with optional BOM.
- ``.csv``: if the first cell of the first row is ``word`` (case-insensitive), the row is treated as a
  header: ``word,label_id,suggestion,priority,enabled`` (extra columns ignored). Otherwise each row is
  ``word`` only or ``word,label_id,suggestion,priority,enabled`` by position; missing trailing cells
  fall back to caller-provided defaults.
"""

from __future__ import annotations

import csv
import io
from typing import Any

_MAX_IMPORT_BYTES = 12 * 1024 * 1024


def _require_under_limit(raw: bytes) -> None:
    if len(raw) > _MAX_IMPORT_BYTES:
        raise ValueError(f"文件过大（上限 { _MAX_IMPORT_BYTES // (1024 * 1024) } MB）")


def _split_ext(filename: str) -> str:
    name = (filename or "").strip().lower()
    if "." not in name:
        return ""
    return name[name.rindex(".") :]


def parse_lexicon_import_bytes(*, raw: bytes, filename: str) -> list[dict[str, Any]]:
    _require_under_limit(raw)
    ext = _split_ext(filename)
    if ext not in (".txt", ".csv"):
        raise ValueError("仅支持 UTF-8 的 .txt 或 .csv（与常见云厂商词库批量导入格式一致：换行分隔或 CSV 模板）")
    text = raw.decode("utf-8-sig")
    if ext == ".txt":
        return _parse_txt(text)
    return _parse_csv(text)


def _parse_txt(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        w = line.strip()
        if not w or w.startswith("#"):
            continue
        rows.append({"word": w})
    if not rows:
        raise ValueError("未解析到任何词条（.txt 需每行一词，UTF-8）")
    return rows


def _parse_csv(text: str) -> list[dict[str, Any]]:
    stream = io.StringIO(text)
    reader = csv.reader(stream)
    table = list(reader)
    if not table:
        raise ValueError("CSV 为空")
    first_cells = [(c or "").strip() for c in table[0]]
    if first_cells and first_cells[0].lower() == "word":
        return _parse_csv_with_header(table)
    return _parse_csv_body_only(table)


def _parse_csv_with_header(table: list[list[str]]) -> list[dict[str, Any]]:
    header = [(c or "").strip().lower() for c in table[0]]
    idx: dict[str, int] = {}
    for i, h in enumerate(header):
        if h and h not in idx:
            idx[h] = i
    if "word" not in idx:
        raise ValueError("CSV 表头需包含 word 列")

    rows: list[dict[str, Any]] = []
    for r in table[1:]:
        if not r or all(not (c or "").strip() for c in r):
            continue

        def cell(key: str) -> str:
            i = idx.get(key)
            if i is None or i >= len(r):
                return ""
            return (r[i] or "").strip()

        w = cell("word")
        if not w:
            continue
        item: dict[str, Any] = {"word": w}
        if cell("label_id"):
            item["label_id"] = _parse_int(cell("label_id"), field="label_id")
        if cell("suggestion"):
            item["suggestion"] = _parse_int(cell("suggestion"), field="suggestion")
        if cell("priority"):
            item["priority"] = _parse_int(cell("priority"), field="priority")
        if cell("enabled"):
            item["enabled"] = _parse_bool_cell(cell("enabled"))
        rows.append(item)

    if not rows:
        raise ValueError("未解析到任何词条（检查 CSV 数据行）")
    return rows


def _parse_csv_body_only(table: list[list[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in table:
        if not r:
            continue
        w = (r[0] or "").strip()
        if not w:
            continue
        item: dict[str, Any] = {"word": w}
        if len(r) >= 2 and (r[1] or "").strip():
            item["label_id"] = _parse_int((r[1] or "").strip(), field="label_id")
        if len(r) >= 3 and (r[2] or "").strip():
            item["suggestion"] = _parse_int((r[2] or "").strip(), field="suggestion")
        if len(r) >= 4 and (r[3] or "").strip():
            item["priority"] = _parse_int((r[3] or "").strip(), field="priority")
        if len(r) >= 5 and (r[4] or "").strip():
            item["enabled"] = _parse_bool_cell((r[4] or "").strip())
        rows.append(item)
    if not rows:
        raise ValueError("未解析到任何词条")
    return rows


def _parse_int(value: str, *, field: str) -> int:
    try:
        return int(str(value).strip(), 10)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 需为整数：{value!r}") from exc


def _parse_bool_cell(value: str) -> bool:
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError(f"enabled 需为 0/1 或 true/false：{value!r}")


def _coerce_enabled(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return _parse_bool_cell(str(value))


def normalize_entries(
    parsed: list[dict[str, Any]],
    *,
    default_label_id: int,
    default_suggestion: int,
    default_priority: int,
    default_enabled: bool,
) -> list[dict[str, Any]]:
    """Fill defaults and coerce to the shape expected by ``lexicon_repo.add_entries``."""

    out: list[dict[str, Any]] = []
    for row in parsed:
        word = str(row.get("word", "")).strip()
        if not word:
            continue
        label_id = int(row.get("label_id", default_label_id))
        suggestion = int(row.get("suggestion", default_suggestion))
        priority = int(row.get("priority", default_priority))
        enabled = _coerce_enabled(row.get("enabled", default_enabled), default_enabled)
        out.append(
            {
                "word": word,
                "label_id": label_id,
                "suggestion": suggestion,
                "priority": priority,
                "enabled": enabled,
            }
        )
    if not out:
        raise ValueError("没有有效词条")
    return out
