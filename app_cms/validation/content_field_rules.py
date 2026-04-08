from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

from app_cms.models.content_meta import CmsContentMeta
from common.utils.django_util import post_like_mapping_to_dict

logger = logging.getLogger(__name__)


class ContentFieldRulesBuilder:
    """Builds per-field validation rules from ``content_meta.fields.columns[].validation``."""

    def build_rules(self, meta: CmsContentMeta, partial: bool) -> dict[str, list[str]]:
        items = meta.field_definition_items()
        if not items:
            raise ValidationError("content_meta.fields.columns must define validation for each column")
        rules: dict[str, list[str]] = {}
        for d in items:
            name = d.get("name")
            if not isinstance(name, str) or not name:
                continue
            rules[name] = self._rules_for_field(d, partial)
        if not rules:
            raise ValidationError("content_meta.fields must define at least one valid column name")
        return rules

    def _rules_for_field(self, d: dict, partial: bool) -> list[str]:
        ftype = str(d.get("type") or "")
        rules = self._base_prefix(d, partial)
        if ftype == "string":
            return rules + ["type:string"]
        if ftype == "text":
            return rules + ["type:text"]
        if ftype == "integer":
            return rules + ["type:integer"]
        if ftype == "date":
            return rules + ["type:date"]
        if ftype == "json":
            return rules + ["type:json"]
        raise ValidationError(f"Unsupported field type: {ftype}")

    def _base_prefix(self, d: dict, partial: bool) -> list[str]:
        if partial:
            if d.get("required") is True:
                return ["sometimes"]
            return ["nullable"]
        if d.get("required") is True:
            return ["required"]
        return ["nullable"]


def validate_item_payload(
    meta: CmsContentMeta,
    raw: dict[str, Any],
    *,
    partial: bool,
) -> dict[str, Any]:
    builder = ContentFieldRulesBuilder()
    rules = builder.build_rules(meta, partial)
    cleaned: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for field_name, rule_list in rules.items():
        present = field_name in raw
        val = raw.get(field_name)
        try:
            coerced = _validate_field(field_name, val, rule_list, present)
            if coerced is not _OMIT:
                cleaned[field_name] = coerced
        except ValidationError as e:
            errors[field_name] = e.messages[0] if e.messages else str(e)

    if errors:
        raise ValidationError(errors)

    return _pick_declared_fields(meta, cleaned)


_OMIT = object()


def _validate_field(name: str, val: Any, rule_list: list[str], present: bool) -> Any:
    sometimes = "sometimes" in rule_list
    required = "required" in rule_list

    if sometimes and not present:
        return _OMIT

    if not present:
        if required:
            raise ValidationError(f"{name} is required")
        return _OMIT

    if val in (None, ""):
        if not required:
            return None
        raise ValidationError(f"{name} is required")

    current: Any = val
    for r in rule_list:
        if r in ("required", "nullable", "sometimes"):
            continue
        if r.startswith("type:"):
            t = r.split(":", 1)[1]
            current = _coerce_type(current, t)
    return current


def _coerce_type(val: Any, t: str) -> Any:
    if t == "string":
        if val is None:
            return None
        return str(val)
    if t == "text":
        if val is None:
            return None
        return str(val)
    if t == "integer":
        try:
            return int(val)
        except (TypeError, ValueError) as e:
            raise ValidationError("must be an integer") from e
    if t == "date":
        return _parse_date_value(val)
    if t == "json":
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except json.JSONDecodeError as e:
                raise ValidationError(f"must be valid JSON: {e}") from e
        if not isinstance(val, (dict, list)):
            raise ValidationError("must be a JSON object or array")
        return val
    raise ValidationError(f"unknown type {t}")


def _parse_date_value(v: Any) -> datetime:
    if isinstance(v, datetime):
        return v
    if not isinstance(v, str):
        raise ValidationError("must be a valid date")
    dt = parse_datetime(v)
    if dt is not None:
        return dt
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::(\d{2}))?", v)
    if m:
        tail = m.group(3) or "00"
        return datetime.fromisoformat(f"{m.group(1)}T{m.group(2)}:{tail}")
    raise ValidationError("must be a valid date")


def _pick_declared_fields(meta: CmsContentMeta, validated: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for d in meta.field_definition_items():
        name = d.get("name")
        if not isinstance(name, str) or not name:
            continue
        if name not in validated:
            continue
        out[name] = validated[name]
    return out


def merge_json_string_fields(meta: CmsContentMeta, raw: Any) -> dict[str, Any]:
    merged = post_like_mapping_to_dict(raw)
    for d in meta.field_definition_items():
        if d.get("type") != "json":
            continue
        name = d.get("name")
        if not isinstance(name, str) or not name:
            continue
        if name not in merged:
            continue
        s = merged.get(name)
        if not isinstance(s, str) or s == "":
            continue
        try:
            merged[name] = json.loads(s)
        except json.JSONDecodeError as e:
            logger.warning(
                "Skipping JSON merge for field %r: invalid JSON (%s)",
                name,
                e,
            )
    return merged
