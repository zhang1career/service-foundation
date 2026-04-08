"""Tests for ``content_meta_fields`` schema helpers."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from app_cms.schema.content_meta_fields import (
    SCHEMA_VERSION,
    column_accessors,
    ddl_column_definition,
    fields_document_hash,
    infer_sql_default,
    normalize_fields_document,
    validate_fields_document,
)


def _minimal_column(
    name: str = "title",
    physical: str = "varchar(128)",
    *,
    nullable: bool = True,
    index: str = "none",
    vtype: str = "string",
    required: bool = False,
) -> dict:
    return {
        "name": name,
        "physical": physical,
        "nullable": nullable,
        "index": index,
        "validation": {"type": vtype, "required": required},
    }


class NormalizeFieldsDocumentTest(SimpleTestCase):
    def test_non_dict_returns_empty_shell(self):
        out = normalize_fields_document([])  # type: ignore[arg-type]
        self.assertEqual(out["schema_version"], SCHEMA_VERSION)
        self.assertEqual(out["columns"], [])
        self.assertEqual(out["indexes"], [])

    def test_merges_explicit_and_column_indexes(self):
        raw = {
            "columns": [
                {
                    **_minimal_column("slug", "varchar(64)", index="unique"),
                }
            ],
            "indexes": [],
        }
        out = normalize_fields_document(raw)
        self.assertEqual(len(out["indexes"]), 1)
        self.assertEqual(out["indexes"][0]["columns"], ["slug"])
        self.assertTrue(out["indexes"][0]["unique"])

    def test_fields_document_hash_stable_for_same_columns(self):
        doc = {"columns": [_minimal_column()]}
        h1 = fields_document_hash(doc)
        h2 = fields_document_hash(doc)
        self.assertEqual(h1, h2)


class ValidateFieldsDocumentTest(SimpleTestCase):
    def test_valid_minimal_document(self):
        fields = normalize_fields_document({"columns": [_minimal_column()]})
        validate_fields_document(fields)

    def test_wrong_schema_version(self):
        fields = {
            "schema_version": 99,
            "columns": [_minimal_column()],
        }
        with self.assertRaises(ValidationError):
            validate_fields_document(fields)

    def test_empty_columns_rejected(self):
        with self.assertRaises(ValidationError):
            validate_fields_document(
                {"schema_version": SCHEMA_VERSION, "columns": []}
            )

    def test_reserved_column_name_rejected(self):
        col = _minimal_column(name="id")
        with self.assertRaises(ValidationError):
            validate_fields_document(
                {"schema_version": SCHEMA_VERSION, "columns": [col]}
            )

    def test_index_unknown_column_rejected(self):
        fields = normalize_fields_document(
            {
                "columns": [_minimal_column()],
                "indexes": [{"columns": ["missing"], "unique": False}],
            }
        )
        with self.assertRaises(ValidationError):
            validate_fields_document(fields)


class DdlAndAccessorsTest(SimpleTestCase):
    def test_column_accessors_maps_names(self):
        cols = [_minimal_column("a"), _minimal_column("b")]
        m = column_accessors(cols)
        self.assertEqual(m["a"], "a")
        self.assertEqual(m["b"], "b")

    def test_ddl_column_definition_includes_backticks(self):
        col = _minimal_column("my_col", "varchar(10)")
        sql = ddl_column_definition(col)
        self.assertIn("`my_col`", sql)
        self.assertIn("varchar(10)", sql)

    def test_infer_sql_default_nullable_none(self):
        col = _minimal_column(nullable=True)
        self.assertIsNone(infer_sql_default(col))
