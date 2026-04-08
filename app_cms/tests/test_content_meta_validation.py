"""Tests for admin/content-meta validation and POST parsing."""

from __future__ import annotations

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import SimpleTestCase

from app_cms.schema.content_meta_fields import SCHEMA_VERSION, normalize_fields_document
from app_cms.validation.content_meta_validation import (
    parse_content_meta_fields_from_post,
    validate_store_meta,
    validate_update_meta,
)


class ParseContentMetaFieldsFromPostTest(SimpleTestCase):
    def test_parses_column_and_validation(self):
        q = QueryDict(mutable=True)
        q["fields[columns][0][name]"] = "title"
        q["fields[columns][0][physical]"] = "varchar(128)"
        q["fields[columns][0][nullable]"] = "on"
        q["fields[columns][0][validation][type]"] = "string"
        q["fields[columns][0][validation][required]"] = "true"

        out = parse_content_meta_fields_from_post(q)
        self.assertEqual(out["schema_version"], SCHEMA_VERSION)
        self.assertEqual(len(out["columns"]), 1)
        col = out["columns"][0]
        self.assertEqual(col["name"], "title")
        self.assertEqual(col["physical"], "varchar(128)")
        self.assertTrue(col["nullable"])
        self.assertEqual(col["validation"]["type"], "string")
        self.assertTrue(col["validation"]["required"])

    def test_parses_index_rows(self):
        q = QueryDict(mutable=True)
        q["fields[columns][0][name]"] = "a"
        q["fields[columns][0][physical]"] = "varchar(8)"
        q["fields[columns][0][nullable]"] = ""
        q["fields[columns][0][validation][type]"] = "string"
        q["fields[indexes][0][columns]"] = "a"
        q["fields[indexes][0][unique]"] = "1"

        out = parse_content_meta_fields_from_post(q)
        self.assertEqual(len(out["indexes"]), 1)
        self.assertEqual(out["indexes"][0]["columns"], ["a"])
        self.assertTrue(out["indexes"][0]["unique"])


class ValidateUpdateMetaTest(SimpleTestCase):
    def test_returns_normalized_fields(self):
        raw = {
            "columns": [
                {
                    "name": "title",
                    "physical": "varchar(64)",
                    "nullable": True,
                    "index": "none",
                    "validation": {"type": "string", "required": False},
                }
            ]
        }
        out = validate_update_meta(fields=raw)
        self.assertIn("fields", out)
        self.assertEqual(out["fields"]["schema_version"], SCHEMA_VERSION)


class ValidateStoreMetaTest(SimpleTestCase):
    @patch("app_cms.validation.content_meta_validation.CmsContentMeta.objects")
    def test_rejects_duplicate_name_without_hitting_db(self, objects_mgr):
        objects_mgr.filter.return_value.exists.return_value = True
        fields = normalize_fields_document(
            {
                "columns": [
                    {
                        "name": "title",
                        "physical": "varchar(64)",
                        "nullable": True,
                        "index": "none",
                        "validation": {"type": "string", "required": False},
                    }
                ]
            }
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_store_meta(name="taken", fields=fields)
        self.assertIn("name", ctx.exception.message_dict)

    @patch("app_cms.validation.content_meta_validation.CmsContentMeta.objects")
    def test_accepts_new_name_when_not_duplicate(self, objects_mgr):
        objects_mgr.filter.return_value.exists.return_value = False
        fields = normalize_fields_document(
            {
                "columns": [
                    {
                        "name": "title",
                        "physical": "varchar(64)",
                        "nullable": True,
                        "index": "none",
                        "validation": {"type": "string", "required": False},
                    }
                ]
            }
        )
        out = validate_store_meta(name="new_route", fields=fields)
        self.assertEqual(out["name"], "new_route")
        self.assertEqual(out["fields"]["schema_version"], SCHEMA_VERSION)
