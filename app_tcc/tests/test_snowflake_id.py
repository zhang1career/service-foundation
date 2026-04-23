"""Unit tests for TCC snowflake id allocation (HTTP mocked)."""

from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from common.consts.response_const import RET_OK

from app_tcc.services.snowflake_id import SnowflakeIdError, allocate_snowflake_int


@override_settings(
    TCC_SNOWFLAKE_ID_URL="https://id.example/snow",
    TCC_SNOWFLAKE_ACCESS_KEY="secret",
    TCC_SNOWFLAKE_HTTP_TIMEOUT_SEC=3.0,
)
class SnowflakeIdTests(SimpleTestCase):
    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_allocate_success(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {"id": " 42 "}}
        mock_sync.return_value = mock_resp

        self.assertEqual(allocate_snowflake_int(), 42)
        mock_sync.assert_called_once()
        self.assertEqual(
            mock_sync.call_args.kwargs["json_body"],
            {"access_key": "secret"},
        )

    @override_settings(
        TCC_SNOWFLAKE_ID_URL="https://{{sf-snowflake}}/snow",
        TCC_SNOWFLAKE_ACCESS_KEY="secret",
        TCC_SNOWFLAKE_HTTP_TIMEOUT_SEC=3.0,
        SERVICE_DISCOVERY_KEY_PREFIX="",
    )
    @patch("common.services.service_discovery.expand._get_redis_client")
    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_allocate_expands_url_placeholder(self, mock_sync, m_grc):
        m_client = MagicMock()
        m_client.get.return_value = "id.internal:443"
        m_grc.return_value = m_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {"id": "7"}}
        mock_sync.return_value = mock_resp
        self.assertEqual(allocate_snowflake_int(), 7)
        self.assertEqual(mock_sync.call_args.kwargs["url"], "https://id.internal:443/snow")

    @override_settings(TCC_SNOWFLAKE_ID_URL="")
    def test_missing_url(self):
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("TCC_SNOWFLAKE_ID_URL", str(ctx.exception))

    @override_settings(TCC_SNOWFLAKE_ACCESS_KEY="")
    def test_missing_access_key(self):
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("TCC_SNOWFLAKE_ACCESS_KEY", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_http_error_raises(self, mock_sync):
        mock_sync.side_effect = httpx.TimeoutException("timeout")
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("HTTP request failed", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_non_2xx_status(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "err"
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("500", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_invalid_json_body(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("not json")
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("not JSON", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_error_code_not_ok(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": 1, "message": "bad"}
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("bad", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_data_not_dict(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": None}
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("data missing", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_id_missing(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {}}
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("data.id missing", str(ctx.exception))

    @patch("app_tcc.services.snowflake_id.request_sync")
    def test_id_not_integer(self, mock_sync):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {"id": "nope"}}
        mock_sync.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("not an integer", str(ctx.exception))
