from __future__ import annotations

from datetime import datetime
from typing import Any

from django.conf import settings

from app_cms.models.content_meta import CmsContentMeta
from app_cms.schema.content_meta_fields import column_accessors


class ContentPayloadSerializer:
    """Serializes a dynamic content row using ``content_meta.fields.columns``."""

    def list_item(self, meta: CmsContentMeta, model) -> dict[str, Any]:
        cols = meta.column_definitions()
        acc_map = column_accessors(cols)
        row: dict[str, Any] = {"id": model.pk, "content_type": meta.name}
        for col in cols:
            cname = col["name"]
            attr = acc_map[cname]
            val = getattr(model, attr, None)
            if isinstance(val, datetime):
                row[cname] = val.isoformat() if val else None
            else:
                row[cname] = val
        if hasattr(model, "ct"):
            row["ct"] = model.ct
        if hasattr(model, "ut"):
            row["ut"] = model.ut
        if getattr(settings, "CMS_EXPOSE_META", True) and hasattr(model, "meta"):
            row["meta"] = model.meta
        return row

    def detail(self, meta: CmsContentMeta, model) -> dict[str, Any]:
        return self.list_item(meta, model)
