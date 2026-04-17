from __future__ import annotations

from unittest import TestCase
from unittest.mock import MagicMock

from django.test import override_settings

from common.services.http.sync_task_ref import SYNC_HTTP_REQUEST_FN_REF
from common.services.task import distributed_tasks as dt


class ImportCallableTest(TestCase):
    def test_import_callable_module_function(self):
        fn = dt._import_callable("json:loads")
        import json

        self.assertIs(fn, json.loads)

    def test_import_callable_nested_qualname(self):
        fn = dt._import_callable("common.services.http.executor:request_sync")
        from common.services.http.executor import request_sync

        self.assertIs(fn, request_sync)

    def test_import_callable_invalid_ref_raises(self):
        with self.assertRaises(ValueError):
            dt._import_callable("no-colon")
        with self.assertRaises(ValueError):
            dt._import_callable("a:b:c")

    def test_import_callable_missing_attribute_raises(self):
        with self.assertRaises(AttributeError):
            dt._import_callable("json:not_a_real_attr_xyz")

    def test_import_callable_non_callable_raises(self):
        with self.assertRaises(TypeError):
            dt._import_callable("json:__version__")


class RestorePayloadDataTest(TestCase):
    def test_restore_bytes_str_json(self):
        self.assertEqual(
            dt._restore_payload_data({"_type": "bytes", "value": "\xff"}),
            b"\xff",
        )
        self.assertEqual(
            dt._restore_payload_data({"_type": "str", "value": "hi"}),
            "hi",
        )
        self.assertEqual(
            dt._restore_payload_data({"_type": "json", "value": {"a": 1}}),
            {"a": 1},
        )

    def test_restore_plain_dict_without_type_passthrough(self):
        self.assertEqual(dt._restore_payload_data({"plain": 1}), {"plain": 1})

    def test_restore_non_dict_passthrough(self):
        self.assertEqual(dt._restore_payload_data(b"raw"), b"raw")


class SyncFnRefAllowlistTest(TestCase):
    @override_settings(CELERY_SYNC_CALL_ALLOWED_REFS=None)
    def test_default_allowlist_contains_http_request_sync(self):
        self.assertIn(SYNC_HTTP_REQUEST_FN_REF, dt._allowed_sync_fn_refs())

    def test_rejects_ref_when_allowlist_empty(self):
        with override_settings(CELERY_SYNC_CALL_ALLOWED_REFS=frozenset()):
            with self.assertRaises(ValueError):
                dt._reject_if_sync_fn_ref_not_allowed(SYNC_HTTP_REQUEST_FN_REF)


class ResultToDictTest(TestCase):
    def test_dict_sets_elapsed_when_missing(self):
        out = dt._result_to_dict({"x": 1}, 42)
        self.assertEqual(out["x"], 1)
        self.assertEqual(out["elapsed_ms"], 42)

    def test_dict_preserves_existing_elapsed_ms(self):
        out = dt._result_to_dict({"elapsed_ms": 5}, 99)
        self.assertEqual(out["elapsed_ms"], 5)

    def test_response_like_object(self):
        resp = MagicMock()
        resp.status_code = 201
        resp.headers = {"X": "y"}
        resp.text = "body"
        resp.request.url = "https://api.example/r"

        out = dt._result_to_dict(resp, 10)
        self.assertEqual(out["status_code"], 201)
        self.assertEqual(out["headers"], {"X": "y"})
        self.assertEqual(out["text"], "body")
        self.assertEqual(out["url"], "https://api.example/r")
        self.assertEqual(out["elapsed_ms"], 10)

    def test_response_like_object_strips_query_from_url(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}
        resp.text = ""
        resp.request.url = "https://api.example/r?token=secret"

        out = dt._result_to_dict(resp, 1)
        self.assertEqual(out["url"], "https://api.example/r")

    def test_invalid_result_raises(self):
        with self.assertRaises(TypeError):
            dt._result_to_dict(42, 1)
