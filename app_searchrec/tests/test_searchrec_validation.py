from django.test import SimpleTestCase

from app_searchrec.validation import normalize_upsert_document_payload, parse_optional_unit_interval


class TestParseOptionalUnitInterval(SimpleTestCase):
    def test_none_is_zero(self):
        self.assertEqual(parse_optional_unit_interval(None, "popularity_score"), 0.0)

    def test_boundaries(self):
        self.assertEqual(parse_optional_unit_interval(0, "x"), 0.0)
        self.assertEqual(parse_optional_unit_interval(1, "x"), 1.0)
        self.assertEqual(parse_optional_unit_interval("0.5", "x"), 0.5)

    def test_above_one_raises(self):
        with self.assertRaisesMessage(ValueError, "must be normalized"):
            parse_optional_unit_interval(1.01, "popularity_score")

    def test_negative_raises(self):
        with self.assertRaisesMessage(ValueError, "must be normalized"):
            parse_optional_unit_interval(-0.001, "freshness_score")

    def test_nan_raises(self):
        with self.assertRaisesMessage(ValueError, "finite"):
            parse_optional_unit_interval(float("nan"), "popularity_score")


class TestNormalizeUpsertDocumentPayload(SimpleTestCase):
    def test_adds_defaults(self):
        out = normalize_upsert_document_payload({"id": "a"})
        self.assertEqual(out["popularity_score"], 0.0)
        self.assertEqual(out["freshness_score"], 0.0)
