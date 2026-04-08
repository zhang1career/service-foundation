"""Tests for CMS DB router and signal wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_cms.db_routers import ReadWriteRouter
from app_cms.models.content_meta import CmsContentMeta
from app_cms.signals import content_meta_drop_physical_table


class ReadWriteRouterTest(SimpleTestCase):
    def test_routes_app_cms_reads_to_cms_rw(self):
        r = ReadWriteRouter()
        self.assertEqual(r.db_for_read(CmsContentMeta), "cms_rw")

    def test_routes_app_cms_writes_to_cms_rw(self):
        r = ReadWriteRouter()
        self.assertEqual(r.db_for_write(CmsContentMeta), "cms_rw")

    def test_allow_migrate_only_on_cms_alias(self):
        r = ReadWriteRouter()
        self.assertTrue(r.allow_migrate("cms_rw", "app_cms"))
        self.assertFalse(r.allow_migrate("default", "app_cms"))


class ContentMetaSignalTest(SimpleTestCase):
    @patch("app_cms.signals.ContentPhysicalTableService")
    def test_post_delete_calls_drop_if_exists(self, svc_cls):
        instance = MagicMock(spec=CmsContentMeta)
        content_meta_drop_physical_table(MagicMock(), instance)
        svc_cls.return_value.drop_if_exists.assert_called_once_with(instance)
