from unittest import TestCase
from unittest.mock import MagicMock, patch

import httpx
from django.test import override_settings

from common.services.http.executor import (
    HttpCallError,
    SYNC_HTTP_REQUEST_FN_REF,
    _normalize_data,
    _queue_for_pool,
    request_async,
    request_sync,
)
from common.services.http.outbound_url import OutboundUrlPolicyError


class HttpExecutorTest(TestCase):
    def test_normalize_data_bytes_and_str(self):
        self.assertEqual(_normalize_data(b"\x01"), {"_type": "bytes", "value": "\x01"})
        self.assertEqual(_normalize_data("abc"), {"_type": "str", "value": "abc"})
        self.assertIsNone(_normalize_data(None))

    def test_normalize_data_non_serializable_raises(self):
        with self.assertRaises(TypeError):
            _normalize_data({"x": {1, 2}})

    def test_normalize_data_json_serializable_dict(self):
        self.assertEqual(
            _normalize_data({"a": 1, "b": [2]}),
            {"_type": "json", "value": {"a": 1, "b": [2]}},
        )

    @override_settings(
        HTTPX_POOL_CELERY_QUEUE={"3rd_party_pl": "q_tp", "webhook_pl": "q_wh"},
        CELERY_TASK_DEFAULT_QUEUE="q_fallback",
    )
    def test_queue_for_pool_uses_mapping_and_default(self):
        self.assertEqual(_queue_for_pool("3rd_party_pl"), "q_tp")
        self.assertEqual(_queue_for_pool("webhook_pl"), "q_wh")
        self.assertEqual(_queue_for_pool("unknown_pool"), "q_fallback")

    @override_settings(
        HTTPX_POOL_CELERY_QUEUE=None,
        CELERY_TASK_DEFAULT_QUEUE="q_only",
    )
    def test_queue_for_pool_empty_when_mapping_none(self):
        self.assertEqual(_queue_for_pool("any_pool"), "q_only")

    def test_request_sync_rejects_loopback_url(self):
        with self.assertRaises(OutboundUrlPolicyError):
            request_sync(method="get", url="http://127.0.0.1/")

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_success(self, get_client_mock):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        client.request.return_value = response
        get_client_mock.return_value = client

        ret = request_sync(method="get", url="http://203.0.113.1/")
        self.assertIs(ret, response)
        client.request.assert_called_once()
        get_client_mock.assert_called_once_with(
            pool_name="3rd_party_pl",
            timeout_sec=None,
        )
        call_kw = client.request.call_args.kwargs
        self.assertEqual(call_kw["method"], "GET")
        self.assertEqual(call_kw["url"], "http://203.0.113.1/")
        self.assertIsNone(call_kw["headers"])
        self.assertIsNone(call_kw["params"])
        self.assertIsNone(call_kw["json"])
        self.assertIsNone(call_kw["content"])
        self.assertIsNone(call_kw["timeout"])
        self.assertIs(call_kw["follow_redirects"], False)

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_forwards_pool_timeout_headers_params_json_and_data(
        self, get_client_mock
    ):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 201
        client.request.return_value = response
        get_client_mock.return_value = client

        ret = request_sync(
            method="post",
            url="http://203.0.113.1/v1",
            pool_name="webhook_pl",
            headers={"X-Req": "1"},
            params={"q": "a"},
            json_body={"a": 1},
            data=b"raw",
            timeout_sec=12.5,
        )
        self.assertIs(ret, response)
        get_client_mock.assert_called_once_with(
            pool_name="webhook_pl",
            timeout_sec=12.5,
        )
        client.request.assert_called_once_with(
            method="POST",
            url="http://203.0.113.1/v1",
            headers={"X-Req": "1"},
            params={"q": "a"},
            json={"a": 1},
            content=b"raw",
            timeout=12.5,
            follow_redirects=False,
        )

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_wraps_httpx_error(self, get_client_mock):
        client = MagicMock()
        client.request.side_effect = httpx.ConnectError("boom")
        get_client_mock.return_value = client

        with self.assertRaises(HttpCallError):
            request_sync(method="get", url="http://203.0.113.1/")

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_http_error_preserves_cause(self, get_client_mock):
        client = MagicMock()
        inner = httpx.TimeoutException("slow")
        client.request.side_effect = inner
        get_client_mock.return_value = client

        with self.assertRaises(HttpCallError) as ctx:
            request_sync(method="get", url="http://203.0.113.1/")
        self.assertIs(ctx.exception.__cause__, inner)

    @patch("common.services.task.sync_call_task")
    def test_request_async_apply_async_payload(self, mock_sync_task):
        mock_apply = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "celery-task-id"
        mock_apply.return_value = mock_task
        mock_sync_task.apply_async = mock_apply

        task_id = request_async(
            method="post",
            url="http://203.0.113.1/hook",
            pool_name="webhook_pl",
            headers={"H": "1"},
            params={"p": "q"},
            json_body={"j": True},
            data=b"\x00",
            timeout_sec=30.0,
        )
        self.assertEqual(task_id, "celery-task-id")
        mock_apply.assert_called_once()
        call_kw = mock_apply.call_args.kwargs["kwargs"]
        self.assertEqual(call_kw["sync_fn_ref"], SYNC_HTTP_REQUEST_FN_REF)
        fn_kw = call_kw["fn_kwargs"]
        self.assertEqual(fn_kw["method"], "POST")
        self.assertEqual(fn_kw["url"], "http://203.0.113.1/hook")
        self.assertEqual(fn_kw["pool_name"], "webhook_pl")
        self.assertEqual(fn_kw["headers"], {"H": "1"})
        self.assertEqual(fn_kw["params"], {"p": "q"})
        self.assertEqual(fn_kw["json_body"], {"j": True})
        self.assertEqual(fn_kw["timeout_sec"], 30.0)
        self.assertEqual(fn_kw["data"], {"_type": "bytes", "value": "\x00"})

    @patch("common.services.task.sync_call_task")
    def test_request_async_explicit_queue_name(self, mock_sync_task):
        mock_apply = MagicMock()
        mock_task = MagicMock()
        mock_task.id = "t2"
        mock_apply.return_value = mock_task
        mock_sync_task.apply_async = mock_apply

        request_async(
            method="get",
            url="http://203.0.113.1/x",
            queue_name="priority",
        )
        self.assertEqual(mock_apply.call_args.kwargs["queue"], "priority")
