"""Unit tests for app_saga.services.snowflake_id (no DB)."""

from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from app_saga.services.snowflake_id import SnowflakeIdError, allocate_snowflake_int
from common.consts.response_const import RET_OK


class SnowflakeIdTests(SimpleTestCase):
    @override_settings(SAGA_SNOWFLAKE_ID_URL="")
    def test_missing_url_raises(self):
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("SAGA_SNOWFLAKE_ID_URL", str(ctx.exception))

    @override_settings(SAGA_SNOWFLAKE_ID_URL="http://id.test/", SAGA_SNOWFLAKE_ACCESS_KEY="")
    def test_missing_access_key_raises(self):
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("SAGA_SNOWFLAKE_ACCESS_KEY", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
        SAGA_SNOWFLAKE_HTTP_TIMEOUT_SEC=3.0,
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_http_error_wraps(self, mock_req):
        mock_req.side_effect = httpx.TimeoutException("t")
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("HTTP", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_non_2xx_raises(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "err"
        mock_req.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("500", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_invalid_json_raises(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("x")
        mock_req.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("JSON", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_error_code_raises(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": 1, "message": "bad"}
        mock_req.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("bad", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_missing_data_raises(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK}
        mock_req.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("data", str(ctx.exception).lower())

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_missing_id_raises(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {}}
        mock_req.return_value = mock_resp
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("id", str(ctx.exception).lower())

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://{{sf-snowflake}}/api/snowflake/id",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
        SERVICE_DISCOVERY_KEY_PREFIX="",
    )
    @patch("common.services.service_discovery.expand._get_redis_client")
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_url_placeholder_expands_from_redis(self, mock_req, m_grc):
        m_client = MagicMock()
        m_client.get.return_value = "snow.test:8080"
        m_grc.return_value = m_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {"id": "1"}}
        mock_req.return_value = mock_resp
        self.assertEqual(allocate_snowflake_int(), 1)
        self.assertEqual(
            mock_req.call_args.kwargs["url"],
            "http://snow.test:8080/api/snowflake/id",
        )

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://{{sf-snowflake}}/api/x",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("common.services.service_discovery.expand._get_redis_client")
    def test_url_placeholder_missing_host_raises(self, m_grc):
        m_client = MagicMock()
        m_client.get.return_value = None
        m_grc.return_value = m_client
        with self.assertRaises(SnowflakeIdError) as ctx:
            allocate_snowflake_int()
        self.assertIn("No data found for service", str(ctx.exception))

    @override_settings(
        SAGA_SNOWFLAKE_ID_URL="http://id.test/",
        SAGA_SNOWFLAKE_ACCESS_KEY="k",
    )
    @patch("app_saga.services.snowflake_id.request_sync")
    def test_success_returns_int(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errorCode": RET_OK, "data": {"id": " 42 "}}
        mock_req.return_value = mock_resp
        self.assertEqual(allocate_snowflake_int(), 42)
        mock_req.assert_called_once()
        self.assertEqual(
            mock_req.call_args.kwargs["json_body"],
            {"access_key": "k"},
        )
