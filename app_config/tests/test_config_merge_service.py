"""Unit tests for condition matching and shallow merge (mocked DB)."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app_config.services.config_merge_service import (
    conditions_hash,
    merge_config_query_result,
    normalize_conditions,
)


class TestNormalizeAndHash(unittest.TestCase):
    def test_normalize_empty(self):
        self.assertEqual(normalize_conditions(None), {})

    def test_normalize_rejects_non_object(self):
        with self.assertRaises(ValueError):
            normalize_conditions([])

    def test_conditions_hash_stable(self):
        a = {"b": 1, "a": 2}
        b = {"a": 2, "b": 1}
        self.assertEqual(conditions_hash(a), conditions_hash(b))


class TestMergeConfigQueryResult(unittest.TestCase):
    def _row(self, pk, ut, cond, value):
        return SimpleNamespace(id=pk, ut=ut, condition=json.dumps(cond), value=json.dumps(value))

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_empty_returns_null_value(self, mock_list):
        mock_list.return_value = []
        out = merge_config_query_result(1, "k", {})
        self.assertIsNone(out["value"])
        self.assertEqual(out["source_ids"], "")
        self.assertEqual(out["audit"]["matched_layers"], [])

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_subset_match_merge_order(self, mock_list):
        mock_list.return_value = [
            self._row(1, 100, {}, {"a": 1}),
            self._row(2, 200, {"env": "prod"}, {"b": 2}),
        ]
        out = merge_config_query_result(1, "k", {"env": "prod"})
        self.assertEqual(out["value"], {"a": 1, "b": 2})
        self.assertEqual(out["source_ids"], "1,2")
        self.assertEqual(len(out["audit"]["matched_layers"]), 2)
        self.assertEqual(out["audit"]["conditions_received"], {"env": "prod"})

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_non_dict_value_stops_merge(self, mock_list):
        mock_list.return_value = [
            self._row(1, 100, {}, {"a": 1}),
            self._row(2, 200, {}, [1, 2]),
        ]
        out = merge_config_query_result(1, "k", {})
        self.assertEqual(out["value"], [1, 2])
        self.assertEqual(out["source_ids"], "1,2")

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_row_missing_condition_key_no_match(self, mock_list):
        mock_list.return_value = [self._row(1, 100, {"env": "prod"}, {"x": 1})]
        out = merge_config_query_result(1, "k", {})
        self.assertIsNone(out["value"])
        self.assertEqual(out["source_ids"], "")

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_invalid_condition_json_row_skipped(self, mock_list):
        mock_list.return_value = [
            SimpleNamespace(id=1, ut=100, condition="not json", value=json.dumps({"a": 1})),
        ]
        out = merge_config_query_result(1, "k", {})
        self.assertIsNone(out["value"])
        self.assertEqual(out["source_ids"], "")

    @patch("app_config.services.config_merge_service.config_entry_repo.list_entries_for_rid_and_key")
    def test_invalid_value_json_skipped_for_merge(self, mock_list):
        mock_list.return_value = [
            self._row(1, 100, {}, {"a": 1}),
            SimpleNamespace(id=2, ut=200, condition="{}", value="not-json"),
        ]
        out = merge_config_query_result(1, "k", {})
        self.assertEqual(out["value"], {"a": 1})
        self.assertEqual(out["source_ids"], "1")
