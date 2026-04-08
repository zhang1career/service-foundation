"""Tests for dynamic model resolution."""

from __future__ import annotations

import uuid

from django.db import models
from django.test import SimpleTestCase

from app_cms.models.content_meta import CmsContentMeta
from app_cms.services.content_model_resolver import (
    ContentModelResolver,
    _class_name_suffix,
    _django_field_for_column,
)


class ClassNameSuffixTest(SimpleTestCase):
    def test_empty_table_returns_default(self):
        self.assertEqual(_class_name_suffix(""), "Tbl")

    def test_splits_non_alnum(self):
        self.assertEqual(_class_name_suffix("foo_bar_baz"), "FooBarBaz")


class DjangoFieldForColumnTest(SimpleTestCase):
    def test_char(self):
        col = {
            "name": "c",
            "physical": "char(10)",
            "nullable": True,
            "index": "none",
        }
        f = _django_field_for_column(col)
        self.assertIsInstance(f, models.CharField)
        self.assertEqual(f.max_length, 10)

    def test_unsupported_physical_raises(self):
        col = {
            "name": "c",
            "physical": "blob",
            "nullable": True,
            "index": "none",
        }
        with self.assertRaisesRegex(ValueError, "Unsupported physical type"):
            _django_field_for_column(col)


class ContentModelResolverBuildTest(SimpleTestCase):
    def test_model_class_returns_subclass_of_model(self):
        name = f"tmdl_{uuid.uuid4().hex[:10]}"
        meta = CmsContentMeta(
            name=name,
            fields={
                "columns": [
                    {
                        "name": "title",
                        "physical": "varchar(64)",
                        "nullable": True,
                        "index": "none",
                        "validation": {"type": "string", "required": False},
                    }
                ]
            },
            ct=1,
            ut=1,
        )
        resolver = ContentModelResolver()
        cls = resolver.model_class(meta)
        self.assertTrue(issubclass(cls, models.Model))
        self.assertEqual(cls._meta.db_table, f"c_{name}")

    def test_model_class_cached_for_same_meta_signature(self):
        name = f"tcache_{uuid.uuid4().hex[:10]}"
        fields = {
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
        meta = CmsContentMeta(name=name, fields=fields, ct=1, ut=1)
        resolver = ContentModelResolver()
        a = resolver.model_class(meta)
        b = resolver.model_class(meta)
        self.assertIs(a, b)
