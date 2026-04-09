"""Tests for searchrec view request parsing helpers."""

from django.test import SimpleTestCase

from app_searchrec.views.searchrec_view import (
    _optional_dict,
    _optional_list,
    _parse_rid,
    _strategy_param,
)


class TestViewHelpers(SimpleTestCase):
    def test_optional_list(self):
        self.assertEqual(_optional_list(None), [])
        self.assertEqual(_optional_list("x"), [])
        self.assertEqual(_optional_list([1, 2]), [1, 2])

    def test_optional_dict(self):
        self.assertEqual(_optional_dict(None), {})
        self.assertEqual(_optional_dict([]), {})
        self.assertEqual(_optional_dict({"a": 1}), {"a": 1})

    def test_strategy_param(self):
        self.assertEqual(_strategy_param(None), "hybrid")
        self.assertEqual(_strategy_param(""), "hybrid")
        self.assertEqual(_strategy_param("ctr_first"), "ctr_first")

    def test_parse_rid(self):
        self.assertEqual(_parse_rid({"rid": 1}), 1)
        with self.assertRaisesMessage(ValueError, "field `rid` is required"):
            _parse_rid({})
        with self.assertRaisesMessage(ValueError, "field `rid` must be a positive integer"):
            _parse_rid({"rid": 0})
