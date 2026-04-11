"""Tests for condition JSON vs condition_meta.field_key subset rule."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app_config.services.config_condition_validate import normalize_and_validate_condition


class TestNormalizeAndValidateCondition(unittest.TestCase):
    @patch("app_config.services.config_condition_validate.condition_field_repo.list_fields_for_rid")
    def test_empty_meta_only_empty_object(self, mock_list):
        mock_list.return_value = []
        self.assertEqual(normalize_and_validate_condition(1, ""), "{}")
        self.assertEqual(normalize_and_validate_condition(1, "{}"), "{}")
        with self.assertRaises(ValueError) as ctx:
            normalize_and_validate_condition(1, '{"env":"prod"}')
        self.assertIn("not declared", str(ctx.exception))

    @patch("app_config.services.config_condition_validate.condition_field_repo.list_fields_for_rid")
    def test_subset_ok_and_canonical(self, mock_list):
        mock_list.return_value = [
            SimpleNamespace(field_key="env"),
            SimpleNamespace(field_key="region"),
        ]
        out = normalize_and_validate_condition(1, '{"region":"cn","env":"prod"}')
        self.assertEqual(out, '{"env":"prod","region":"cn"}')

    @patch("app_config.services.config_condition_validate.condition_field_repo.list_fields_for_rid")
    def test_extra_key_rejected(self, mock_list):
        mock_list.return_value = [SimpleNamespace(field_key="env")]
        with self.assertRaises(ValueError) as ctx:
            normalize_and_validate_condition(1, '{"env":"a","other":1}')
        self.assertIn("other", str(ctx.exception))

    @patch("app_config.services.config_condition_validate.condition_field_repo.list_fields_for_rid")
    def test_invalid_json(self, mock_list):
        mock_list.return_value = []
        with self.assertRaises(ValueError) as ctx:
            normalize_and_validate_condition(1, "{")
        self.assertIn("JSON", str(ctx.exception))

    @patch("app_config.services.config_condition_validate.condition_field_repo.list_fields_for_rid")
    def test_not_object(self, mock_list):
        mock_list.return_value = []
        with self.assertRaises(ValueError) as ctx:
            normalize_and_validate_condition(1, "[]")
        self.assertIn("object", str(ctx.exception))
