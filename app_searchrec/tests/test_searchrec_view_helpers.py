"""Tests for searchrec view request parsing helpers."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_searchrec.views.searchrec_view import (
    _resolve_reg_id_from_payload,
    _strategy_param,
)
from common.enums.service_reg_status_enum import ServiceRegStatus


class TestViewHelpers(SimpleTestCase):
    def test_strategy_param(self):
        self.assertEqual(_strategy_param(None), "hybrid")
        self.assertEqual(_strategy_param(""), "hybrid")
        self.assertEqual(_strategy_param("ctr_first"), "ctr_first")

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status")
    def test_resolve_reg_id_ok(self, get_reg):
        get_reg.return_value = MagicMock(id=42)
        self.assertEqual(_resolve_reg_id_from_payload({"access_key": "  abc  "}), 42)
        get_reg.assert_called_once_with("abc", ServiceRegStatus.ENABLED)

    def test_resolve_reg_id_missing_access_key(self):
        with self.assertRaisesMessage(ValueError, "field `access_key` is required"):
            _resolve_reg_id_from_payload({})

    @patch("app_searchrec.views.searchrec_view.get_reg_by_access_key_and_status", return_value=None)
    def test_resolve_reg_id_not_found(self, _get):
        with self.assertRaisesMessage(ValueError, "invalid or inactive access_key"):
            _resolve_reg_id_from_payload({"access_key": "nope"})
