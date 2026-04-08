from __future__ import annotations

from django.db import models
from django.db.models import QuerySet

from common.utils.date_util import get_now_timestamp_ms

# Dynamic row tables: ``c_{meta.name}`` (must stay within identifier limits with the prefix).
CMS_DYNAMIC_TABLE_PREFIX = "c_"


class CmsContentMetaQuerySet(QuerySet):
    def by_route_segment(self, segment: str) -> CmsContentMeta | None:
        return self.filter(name=segment).first()


class CmsContentMeta(models.Model):
    """Content type definition. ``fields`` JSON drives DDL (columns, indexes) and API validation."""

    name = models.CharField(max_length=64, unique=True)
    fields = models.JSONField()
    ct = models.BigIntegerField()
    ut = models.BigIntegerField()

    objects = CmsContentMetaQuerySet.as_manager()

    class Meta:
        db_table = "content_meta"

    def save(self, *args, **kwargs) -> None:
        now = get_now_timestamp_ms()
        if self.pk is None and self.ct is None:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)

    def column_definitions(self) -> list[dict]:
        raw = self.fields
        if not isinstance(raw, dict):
            return []
        cols = raw.get("columns")
        if not isinstance(cols, list):
            return []
        return [x for x in cols if isinstance(x, dict)]

    def field_definition_items(self) -> list[dict]:
        """Validation rules for ``validate_item_payload`` — one item per column with ``validation``."""
        out: list[dict] = []
        for col in self.column_definitions():
            v = col.get("validation")
            if not isinstance(v, dict):
                continue
            item = dict(v)
            item["name"] = col["name"]
            out.append(item)
        return out

    @property
    def field_definition_count(self) -> int:
        return len(self.column_definitions())

    def route_segment(self) -> str:
        return self.name

    def physical_table_name(self) -> str:
        return f"{CMS_DYNAMIC_TABLE_PREFIX}{self.name}"

    @classmethod
    def find_by_route_segment(cls, segment: str) -> CmsContentMeta | None:
        return cls.objects.by_route_segment(segment)
