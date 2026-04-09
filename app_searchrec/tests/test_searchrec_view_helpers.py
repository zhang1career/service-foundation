"""Tests for searchrec view request parsing helpers."""

from django.test import SimpleTestCase

from app_searchrec.views.searchrec_view import _optional_dict, _optional_list, _strategy_param


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
