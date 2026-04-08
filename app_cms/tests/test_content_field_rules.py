"""Tests for ``content_field_rules`` validation and coercion."""

from __future__ import annotations

import logging
from datetime import datetime
from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from app_cms.validation.content_field_rules import (
    ContentFieldRulesBuilder,
    merge_json_string_fields,
    validate_item_payload,
)


def _meta_items(*items: dict) -> MagicMock:
    m = MagicMock()
    m.field_definition_items = MagicMock(return_value=list(items))
    return m


class ContentFieldRulesBuilderTest(SimpleTestCase):
    def test_build_rules_requires_at_least_one_field(self):
        meta = _meta_items()
        meta.field_definition_items.return_value = []
        builder = ContentFieldRulesBuilder()
        with self.assertRaises(ValidationError):
            builder.build_rules(meta, partial=False)

    def test_build_rules_skips_invalid_names_then_empty_rules_raises(self):
        meta = _meta_items({"name": "", "type": "string"})
        builder = ContentFieldRulesBuilder()
        with self.assertRaises(ValidationError):
            builder.build_rules(meta, partial=False)

    def test_unsupported_field_type_raises(self):
        meta = _meta_items({"name": "x", "type": "blob"})
        builder = ContentFieldRulesBuilder()
        with self.assertRaisesRegex(ValidationError, "Unsupported field type"):
            builder._rules_for_field({"name": "x", "type": "blob"}, partial=False)

    def test_base_prefix_partial_required_uses_sometimes(self):
        builder = ContentFieldRulesBuilder()
        rules = builder._base_prefix({"required": True}, partial=True)
        self.assertEqual(rules, ["sometimes"])

    def test_base_prefix_partial_optional_uses_nullable(self):
        builder = ContentFieldRulesBuilder()
        rules = builder._base_prefix({"required": False}, partial=True)
        self.assertEqual(rules, ["nullable"])


class ValidateItemPayloadTest(SimpleTestCase):
    def _meta_one_string(self, *, required: bool) -> MagicMock:
        return _meta_items(
            {
                "name": "title",
                "type": "string",
                "required": required,
            }
        )

    def test_full_required_success(self):
        meta = self._meta_one_string(required=True)
        out = validate_item_payload(meta, {"title": "hello"}, partial=False)
        self.assertEqual(out, {"title": "hello"})

    def test_full_required_missing_raises(self):
        meta = self._meta_one_string(required=True)
        with self.assertRaises(ValidationError) as ctx:
            validate_item_payload(meta, {}, partial=False)
        self.assertIn("title", ctx.exception.message_dict)

    def test_full_nullable_omitted_field_omitted_from_output(self):
        meta = self._meta_one_string(required=False)
        out = validate_item_payload(meta, {}, partial=False)
        self.assertEqual(out, {})

    def test_partial_sometimes_missing_field_skipped(self):
        meta = _meta_items(
            {
                "name": "title",
                "type": "string",
                "required": True,
            }
        )
        out = validate_item_payload(meta, {}, partial=True)
        self.assertEqual(out, {})

    def test_integer_coercion(self):
        meta = _meta_items({"name": "n", "type": "integer", "required": True})
        out = validate_item_payload(meta, {"n": "42"}, partial=False)
        self.assertEqual(out, {"n": 42})

    def test_integer_invalid_raises(self):
        meta = _meta_items({"name": "n", "type": "integer", "required": True})
        with self.assertRaises(ValidationError) as ctx:
            validate_item_payload(meta, {"n": "x"}, partial=False)
        self.assertIn("n", ctx.exception.message_dict)

    def test_json_object_accepts_dict(self):
        meta = _meta_items({"name": "data", "type": "json", "required": True})
        out = validate_item_payload(meta, {"data": {"a": 1}}, partial=False)
        self.assertEqual(out, {"data": {"a": 1}})

    def test_json_parses_string(self):
        meta = _meta_items({"name": "data", "type": "json", "required": True})
        out = validate_item_payload(meta, {"data": '[1, 2]'}, partial=False)
        self.assertEqual(out, {"data": [1, 2]})

    def test_json_invalid_string_raises(self):
        meta = _meta_items({"name": "data", "type": "json", "required": True})
        with self.assertRaises(ValidationError) as ctx:
            validate_item_payload(meta, {"data": "not-json"}, partial=False)
        self.assertIn("data", ctx.exception.message_dict)

    def test_date_iso_string(self):
        meta = _meta_items({"name": "d", "type": "date", "required": True})
        out = validate_item_payload(meta, {"d": "2024-01-15T10:30:00Z"}, partial=False)
        self.assertIsInstance(out["d"], datetime)

    def test_date_fallback_without_seconds(self):
        meta = _meta_items({"name": "d", "type": "date", "required": True})
        out = validate_item_payload(meta, {"d": "2024-01-15 10:30"}, partial=False)
        self.assertIsInstance(out["d"], datetime)
        self.assertEqual(out["d"].minute, 30)

    def test_date_non_string_raises(self):
        meta = _meta_items({"name": "d", "type": "date", "required": True})
        with self.assertRaises(ValidationError):
            validate_item_payload(meta, {"d": 123}, partial=False)

    def test_empty_string_nullable_becomes_none(self):
        meta = _meta_items({"name": "title", "type": "string", "required": False})
        out = validate_item_payload(meta, {"title": ""}, partial=False)
        self.assertEqual(out, {"title": None})


class MergeJsonStringFieldsTest(SimpleTestCase):
    def test_invalid_json_logs_warning_and_keeps_string(self):
        meta = _meta_items(
            {
                "name": "payload",
                "type": "json",
                "required": False,
            }
        )
        raw = {"payload": "{not json"}
        with self.assertLogs(
            "app_cms.validation.content_field_rules", level=logging.WARNING
        ) as captured:
            out = merge_json_string_fields(meta, raw)
        self.assertEqual(out["payload"], "{not json")
        self.assertTrue(any("Skipping JSON merge" in line for line in captured.output))

