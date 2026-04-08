from __future__ import annotations

from django.core.paginator import Paginator

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_model_resolver import ContentModelResolver


class ConsoleContentReadService:
    def __init__(self, resolver: ContentModelResolver | None = None) -> None:
        self._resolver = resolver or ContentModelResolver()

    def paginate_all(self, meta: CmsContentMeta, page: int, per_page: int):
        cls = self._resolver.model_class(meta)
        rel = self._resolver.eager_select_related(meta)
        qs = cls.objects.all().order_by("-id")
        if rel:
            qs = qs.select_related(*rel)
        paginator = Paginator(qs, per_page)
        return paginator.get_page(page)
