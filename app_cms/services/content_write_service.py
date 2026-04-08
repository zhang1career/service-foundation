from __future__ import annotations

from django.db import models
from django.http import Http404

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_model_resolver import ContentModelResolver


class ContentWriteService:
    def __init__(self, resolver: ContentModelResolver | None = None) -> None:
        self._resolver = resolver or ContentModelResolver()

    def store(self, meta: CmsContentMeta, attributes: dict) -> models.Model:
        cls = self._resolver.model_class(meta)
        obj = cls()
        self._apply_attributes(obj, attributes)
        obj.save()
        return self._fresh_with_relations(meta, obj)

    def update(self, meta: CmsContentMeta, record_id: int, attributes: dict) -> models.Model:
        cls = self._resolver.model_class(meta)
        obj = cls.objects.filter(pk=record_id).first()
        if obj is None:
            raise Http404("Not found")
        self._apply_attributes(obj, attributes)
        obj.save()
        return self._fresh_with_relations(meta, obj)

    def destroy(self, meta: CmsContentMeta, record_id: int) -> None:
        cls = self._resolver.model_class(meta)
        deleted, _ = cls.objects.filter(pk=record_id).delete()
        if deleted == 0:
            raise Http404("Not found")

    def _apply_attributes(self, obj: models.Model, attributes: dict) -> None:
        for k, v in attributes.items():
            if hasattr(obj, k):
                setattr(obj, k, v)

    def _fresh_with_relations(self, meta: CmsContentMeta, obj: models.Model) -> models.Model:
        rel = self._resolver.eager_select_related(meta)
        qs = type(obj).objects.filter(pk=obj.pk)
        if rel:
            qs = qs.select_related(*rel)
        return qs.get()
