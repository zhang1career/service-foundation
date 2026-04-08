"""Tests for small helpers: utils, enums, media payload, console form values."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from app_cms.enums.content_enums import ContentStatus, ProductStockStatus
from app_cms.models.content_meta import CMS_DYNAMIC_TABLE_PREFIX, CmsContentMeta
from app_cms.models.media_file import CmsMediaFile, MEDIA_FILE_STATUS_READY
from app_cms.services.media_payload_builder import media_payload_from_model
from app_cms.support.console_form_value import attribute_for_field


class CmsContentMetaNamingTest(SimpleTestCase):
    def test_physical_table_name_uses_prefix(self):
        m = CmsContentMeta(name="blog", fields={}, ct=0, ut=0)
        self.assertEqual(m.physical_table_name(), f"{CMS_DYNAMIC_TABLE_PREFIX}blog")


class MediaPayloadBuilderTest(SimpleTestCase):
    def test_none_returns_none(self):
        self.assertIsNone(media_payload_from_model(None))

    def test_maps_fields(self):
        m = MagicMock(spec=CmsMediaFile)
        m.pk = 9
        m.cdn_url = "https://cdn/x"
        m.mime_type = 1
        m.is_ready.return_value = True
        out = media_payload_from_model(m)
        self.assertEqual(out["id"], 9)
        self.assertEqual(out["cdn_url"], "https://cdn/x")
        self.assertTrue(out["ready"])


class ConsoleFormValueTest(SimpleTestCase):
    def test_date_formats_iso_without_tz_suffix(self):
        model = MagicMock()
        dt = datetime(2024, 3, 2, 15, 30, 0, tzinfo=timezone.utc)
        model.published_at = dt
        s = attribute_for_field(model, "published_at", "date")
        self.assertEqual(s, "2024-03-02T15:30")

    def test_json_dict_encodes(self):
        model = MagicMock()
        model.data = {"a": 1}
        s = attribute_for_field(model, "data", "json")
        self.assertIn('"a"', s)

    def test_json_none_returns_empty_string(self):
        model = MagicMock()
        model.data = None
        self.assertEqual(attribute_for_field(model, "data", "json"), "")


class ContentEnumsTest(SimpleTestCase):
    def test_content_status_labels(self):
        self.assertEqual(ContentStatus.DRAFT.label(), "draft")
        self.assertEqual(ContentStatus.PUBLISHED.label(), "published")

    def test_product_stock_labels(self):
        self.assertEqual(ProductStockStatus.IN_STOCK.label(), "in_stock")


class MediaFileReadyConstantTest(SimpleTestCase):
    def test_is_ready_true_when_status_matches_constant(self):
        class Row:
            status = MEDIA_FILE_STATUS_READY

        self.assertTrue(CmsMediaFile.is_ready(Row()))
