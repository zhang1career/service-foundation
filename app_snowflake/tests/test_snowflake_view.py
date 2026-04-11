"""Tests for Snowflake ID API (POST + access_key → reg.rid)."""
import json
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_snowflake.views.snowflake_view import SnowflakeDetailView
from common.consts.response_const import RET_INVALID_PARAM


class _FakeReg:
    def __init__(self, pk: int):
        self.id = pk


class SnowflakeDetailViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_snowflake.views.snowflake_view.generate_id")
    @patch("app_snowflake.views.snowflake_view.get_reg_by_access_key_and_status")
    def test_post_returns_ok_with_rid(self, mock_get_reg, mock_generate_id):
        mock_get_reg.return_value = _FakeReg(42)
        mock_generate_id.return_value = {
            "id": "1",
            "rid": 42,
            "datacenter_id": 0,
            "machine_id": 0,
            "recount": 0,
            "business_id": 2,
            "timestamp": 0,
            "sequence": 0,
        }
        request = self.factory.post(
            "/api/snowflake/id",
            data={"access_key": "k1"},
            format="json",
        )
        response = SnowflakeDetailView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["errorCode"], 0)
        self.assertEqual(payload["data"]["rid"], 42)
        mock_get_reg.assert_called_once()
        mock_generate_id.assert_called_once_with(42)

    @patch("app_snowflake.views.snowflake_view.get_reg_by_access_key_and_status", return_value=None)
    def test_post_invalid_access_key_returns_ret_invalid_param(self, _mock):
        request = self.factory.post(
            "/api/snowflake/id",
            data={"access_key": "unknown"},
            format="json",
        )
        response = SnowflakeDetailView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
