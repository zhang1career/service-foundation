from __future__ import annotations

import re
from typing import Any

from django.db import models

from app_cms.models.content_meta import CmsContentMeta
from app_cms.schema.content_meta_fields import (
    column_accessors,
    column_allows_sql_null,
    column_is_unique,
    fields_document_hash,
)
from common.utils.date_util import get_now_timestamp_ms

_MODEL_CACHE: dict[tuple[Any, str, str], type[models.Model]] = {}

_CHAR_RE = re.compile(r"^char\((\d+)\)$")
_VARCHAR_RE = re.compile(r"^varchar\((\d+)\)$")


class ContentModelResolver:
    """Builds a concrete Django model class from ``content_meta.fields.columns``."""

    def model_class(self, meta: CmsContentMeta) -> type[models.Model]:
        table = meta.physical_table_name()
        fields_doc = meta.fields if isinstance(meta.fields, dict) else {}
        h = fields_document_hash(fields_doc)
        key = (meta.pk, table, h)
        cached = _MODEL_CACHE.get(key)
        if cached is not None:
            return cached
        cls = self._build_model(meta, table, fields_doc)
        _MODEL_CACHE[key] = cls
        return cls

    def eager_select_related(self, meta: CmsContentMeta) -> list[str]:
        return []

    def _build_model(self, meta: CmsContentMeta, table: str, fields_doc: dict[str, Any]) -> type[models.Model]:
        columns = fields_doc.get("columns")
        if not isinstance(columns, list):
            raise ValueError("content_meta.fields.columns is missing")
        accessors = column_accessors(columns)
        attrs: dict[str, Any] = {}
        for col in columns:
            if not isinstance(col, dict):
                continue
            cname = col["name"]
            attr = accessors[cname]
            attrs[attr] = _django_field_for_column(col)

        attrs["ct"] = models.PositiveBigIntegerField(default=0)
        attrs["ut"] = models.PositiveBigIntegerField(default=0)

        class Meta:
            app_label = "app_cms"
            db_table = table

        attrs["Meta"] = Meta
        attrs["__module__"] = __name__
        attrs["objects"] = models.Manager()

        def save(self, *args, **kwargs):
            ts = get_now_timestamp_ms()
            if self.pk is None:
                self.ct = ts
                self.ut = ts
            else:
                self.ut = ts
            super(type(self), self).save(*args, **kwargs)

        attrs["save"] = save

        suffix = _class_name_suffix(table)
        return type(f"CmsDynRow{suffix}", (models.Model,), attrs)


def _class_name_suffix(table: str) -> str:
    parts = [p for p in re.split(r"[^a-zA-Z0-9]+", table) if p]
    if not parts:
        return "Tbl"
    return "".join(p[0].upper() + p[1:] for p in parts)


def _django_field_for_column(col: dict[str, Any]) -> models.Field:
    physical = col["physical"]
    nullable = column_allows_sql_null(col)
    unique = column_is_unique(col)

    char_m = _CHAR_RE.match(physical)
    if char_m:
        n = int(char_m.group(1))
        return models.CharField(max_length=n, null=nullable, blank=nullable, unique=unique)
    varchar_m = _VARCHAR_RE.match(physical)
    if varchar_m:
        n = int(varchar_m.group(1))
        return models.CharField(max_length=n, null=nullable, blank=nullable, unique=unique)
    if physical in ("text", "longtext"):
        return models.TextField(null=nullable, blank=nullable)
    if physical == "bigint unsigned":
        return models.PositiveBigIntegerField(null=nullable, blank=nullable)
    if physical == "int unsigned":
        return models.PositiveIntegerField(null=nullable, blank=nullable)
    if physical == "tinyint unsigned":
        return models.PositiveSmallIntegerField(null=nullable, blank=nullable)
    if physical in ("datetime(6)", "datetime"):
        return models.DateTimeField(null=nullable, blank=nullable)
    if physical == "json":
        return models.JSONField(null=nullable, blank=nullable)
    raise ValueError(f"Unsupported physical type: {physical!r}")
