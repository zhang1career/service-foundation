from unittest import TestCase
from unittest.mock import MagicMock, patch

import httpx

from common.services.http.executor import HttpCallError, _normalize_data, _queue_for_pool, request_sync


class HttpExecutorTest(TestCase):
    def test_normalize_data_bytes_and_str(self):
        self.assertEqual(_normalize_data(b"\x01"), {"_type": "bytes", "value": "\x01"})
        self.assertEqual(_normalize_data("abc"), {"_type": "str", "value": "abc"})
        self.assertIsNone(_normalize_data(None))

    def test_normalize_data_non_serializable_raises(self):
        with self.assertRaises(TypeError):
            _normalize_data({"x": {1, 2}})

    def test_queue_for_pool(self):
        self.assertEqual(_queue_for_pool("avatar_http_pool"), "avatar")
        self.assertEqual(_queue_for_pool("webhook_pool"), "webhook")
        self.assertEqual(_queue_for_pool("thirdparty_pool"), "thirdparty")

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_success(self, get_client_mock):
        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        client.request.return_value = response
        get_client_mock.return_value = client

        ret = request_sync(method="get", url="https://example.com")
        self.assertIs(ret, response)
        client.request.assert_called_once()
        get_client_mock.assert_called_once_with(
            pool_name="thirdparty_pool",
            timeout_sec=None,
        )
        call_kw = client.request.call_args.kwargs
        self.assertEqual(call_kw["method"], "GET")
        self.assertEqual(call_kw["url"], "https://example.com")
        self.assertIsNone(call_kw["headers"])
        self.assertIsNone(call_kw["params"])
        self.assertIsNone(call_kw["json"])
        self.assertIsNone(call_kw["content"])
        self.assertIsNone(call_kw["timeout"])

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
            url="https://api.example/v1",
            pool_name="webhook_pool",
            headers={"X-Req": "1"},
            params={"q": "a"},
            json_body={"a": 1},
            data=b"raw",
            timeout_sec=12.5,
        )
        self.assertIs(ret, response)
        get_client_mock.assert_called_once_with(
            pool_name="webhook_pool",
            timeout_sec=12.5,
        )
        client.request.assert_called_once_with(
            method="POST",
            url="https://api.example/v1",
            headers={"X-Req": "1"},
            params={"q": "a"},
            json={"a": 1},
            content=b"raw",
            timeout=12.5,
        )

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_wraps_httpx_error(self, get_client_mock):
        client = MagicMock()
        client.request.side_effect = httpx.ConnectError("boom")
        get_client_mock.return_value = client

        with self.assertRaises(HttpCallError):
            request_sync(method="get", url="https://example.com")

    @patch("common.services.http.executor.get_http_client")
    def test_request_sync_http_error_preserves_cause(self, get_client_mock):
        client = MagicMock()
        inner = httpx.TimeoutException("slow")
        client.request.side_effect = inner
        get_client_mock.return_value = client

        with self.assertRaises(HttpCallError) as ctx:
            request_sync(method="get", url="https://example.com")
        self.assertIs(ctx.exception.__cause__, inner)
