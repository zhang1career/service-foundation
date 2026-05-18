"""Tests for ``ContentReadService`` ordering and detail paths."""

from __future__ import annotations

from unittest.mock import MagicMock

from django.http import Http404
from django.test import SimpleTestCase

from app_cms.services.content_read_service import ContentReadService, _list_order_by_field


class _Field:
    def __init__(self, name: str) -> None:
        self.name = name


class ListOrderByFieldTest(SimpleTestCase):
    def test_prefers_published_at_when_present(self):
        model_cls = MagicMock()
        model_cls._meta.get_fields.return_value = [
            _Field("id"),
            _Field("published_at"),
        ]
        self.assertEqual(_list_order_by_field(model_cls), "-published_at")

    def test_falls_back_to_id(self):
        model_cls = MagicMock()
        model_cls._meta.get_fields.return_value = [_Field("id")]
        self.assertEqual(_list_order_by_field(model_cls), "-id")


class ContentReadServiceDetailTest(SimpleTestCase):
    def test_detail_by_pks_empty(self):
        resolver = MagicMock()
        svc = ContentReadService(resolver=resolver)
        self.assertEqual(svc.detail_by_pks(MagicMock(), []), [])

    def test_detail_by_pks_preserves_order_and_skips_missing(self):
        resolver = MagicMock()
        meta = MagicMock()
        serializer = MagicMock()
        serializer.detail.side_effect = lambda m, obj: {"id": obj.pk, "title": f"t{obj.pk}"}

        o1 = MagicMock()
        o1.pk = 10
        o2 = MagicMock()
        o2.pk = 20
        dyn = MagicMock()
        dyn.objects.filter.return_value = [o2, o1]
        resolver.model_class.return_value = dyn
        resolver.eager_select_related.return_value = []

        svc = ContentReadService(resolver=resolver, serializer=serializer)
        out = svc.detail_by_pks(meta, [20, 99, 10])
        self.assertEqual(out, [{"id": 20, "title": "t20"}, {"id": 10, "title": "t10"}])
        dyn.objects.filter.assert_called_once_with(pk__in=[20, 99, 10])

    def test_detail_by_pk_raises_404_when_row_missing(self):
        resolver = MagicMock()
        dyn = MagicMock()
        qs = MagicMock()
        qs.first.return_value = None
        dyn.objects.filter.return_value = qs
        resolver.model_class.return_value = dyn
        resolver.eager_select_related.return_value = []

        svc = ContentReadService(resolver=resolver)
        meta = MagicMock()
        with self.assertRaises(Http404):
            svc.detail_by_pk(meta, 999)
