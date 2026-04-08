from __future__ import annotations

from django.core.paginator import Paginator
from django.http import Http404

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_model_resolver import ContentModelResolver
from app_cms.services.content_payload_serializer import ContentPayloadSerializer


def _list_order_by_field(cls) -> str:
    names = {f.name for f in cls._meta.get_fields()}
    if "published_at" in names:
        return "-published_at"
    return "-id"


class ContentReadService:
    """Public API: list and detail by primary key ``id``."""

    def __init__(
        self,
        resolver: ContentModelResolver | None = None,
        serializer: ContentPayloadSerializer | None = None,
    ) -> None:
        self._resolver = resolver or ContentModelResolver()
        self._serializer = serializer or ContentPayloadSerializer()

    def paginate_published(self, meta: CmsContentMeta, page: int, per_page: int):
        cls = self._resolver.model_class(meta)
        rel = self._resolver.eager_select_related(meta)
        qs = cls.objects.all().order_by(_list_order_by_field(cls))
        if rel:
            qs = qs.select_related(*rel)
        paginator = Paginator(qs, per_page)
        return paginator.get_page(page)

    def detail_by_pk(self, meta: CmsContentMeta, record_id: int) -> dict:
        cls = self._resolver.model_class(meta)
        rel = self._resolver.eager_select_related(meta)
        qs = cls.objects.filter(pk=record_id)
        if rel:
            qs = qs.select_related(*rel)
        obj = qs.first()
        if obj is None:
            raise Http404("Not found")
        return self._serializer.detail(meta, obj)

    def list_item_array(self, meta: CmsContentMeta, model) -> dict:
        return self._serializer.list_item(meta, model)
