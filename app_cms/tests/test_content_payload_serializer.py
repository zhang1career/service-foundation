"""Tests for ``ContentPayloadSerializer``."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from app_cms.services.content_payload_serializer import ContentPayloadSerializer


class ContentPayloadSerializerTest(SimpleTestCase):
    def test_list_item_maps_columns_and_datetimes(self):
        meta = MagicMock()
        meta.name = "article"
        meta.column_definitions.return_value = [
            {"name": "title"},
            {"name": "published_at"},
        ]
        model = MagicMock()
        model.pk = 5
        model.title = "Hi"
        model.published_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

        row = ContentPayloadSerializer().list_item(meta, model)
        self.assertEqual(row["id"], 5)
        self.assertEqual(row["content_type"], "article")
        self.assertEqual(row["title"], "Hi")
        self.assertIn("2024-06-01", row["published_at"])

    @override_settings(CMS_EXPOSE_META=False)
    def test_meta_field_hidden_when_setting_off(self):
        meta = MagicMock()
        meta.name = "x"
        meta.column_definitions.return_value = [{"name": "title"}]
        model = MagicMock()
        model.pk = 1
        model.title = "a"
        model.meta = {"k": "v"}

        row = ContentPayloadSerializer().list_item(meta, model)
        self.assertNotIn("meta", row)
