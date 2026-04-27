"""Unit tests for app_saga.services.outbound_http (no DB)."""

from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from app_saga.services import outbound_http
from common.consts.response_const import RET_OK
from common.utils.service_url_template import ServiceUrlResolutionError


class OutboundHttpTests(SimpleTestCase):
    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @override_settings(SAGA_OUTBOUND_TIMEOUT_SEC=12.0)
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_uses_settings_timeout_when_none(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"errorCode": RET_OK}
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={"a": 1},
            timeout_sec=None,
        )
        self.assertEqual(st, 200)
        self.assertEqual(err, "")
        self.assertIsInstance(data, dict)
        mock_req.assert_called_once()
        self.assertEqual(mock_req.call_args.kwargs["timeout_sec"], 12.0)
        self.assertIsNone(mock_req.call_args.kwargs.get("headers"))

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_forwards_extra_headers(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"errorCode": RET_OK}
        mock_req.return_value = mock_resp
        outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
            extra_headers={"X-Request-Id": "rid-42"},
        )
        self.assertEqual(
            mock_req.call_args.kwargs["headers"],
            {"X-Request-Id": "rid-42"},
        )

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_expands_templated_url_before_request(
        self, mock_req, mock_expand
    ):
        mock_expand.return_value = "http://host:1/action"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"errorCode": RET_OK}
        mock_req.return_value = mock_resp
        st, err, _data = outbound_http.call_saga_endpoint(
            url="http://{{order-svc}}/action",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 200)
        self.assertEqual(err, "")
        mock_expand.assert_called_once_with("http://{{order-svc}}/action")
        self.assertEqual(mock_req.call_args.kwargs["url"], "http://host:1/action")

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_substitutes_context_placeholders_after_expand(
        self, mock_req, mock_expand
    ):
        mock_expand.return_value = "http://host:1/s/{{idem_key}}"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        mock_resp.json.return_value = {"errorCode": RET_OK}
        mock_req.return_value = mock_resp
        outbound_http.call_saga_endpoint(
            url="http://{{svc}}/s/{{idem_key}}",
            json_body={},
            timeout_sec=1.0,
            url_template_variables={"idem_key": "777"},
        )
        self.assertEqual(mock_req.call_args.kwargs["url"], "http://host:1/s/777")

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_unresolved_placeholder_does_not_request(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://host/p/{{other_key}}",
            json_body={},
            timeout_sec=1.0,
            url_template_variables={"idem_key": "1"},
        )
        self.assertEqual(st, 0)
        self.assertIn("other_key", err)
        self.assertIsNone(data)
        mock_req.assert_not_called()

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_resolution_error_returns_zero(self, mock_req, mock_expand):
        mock_expand.side_effect = ServiceUrlResolutionError("no service")
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://{{missing}}/a",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 0)
        self.assertIn("no service", err)
        self.assertIsNone(data)
        mock_req.assert_not_called()

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_http_error_returns_zero_status(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_req.side_effect = httpx.ConnectError("boom")
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 0)
        self.assertIn("boom", err)
        self.assertIsNone(data)

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_non_2xx_returns_body_snippet(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "upstream" * 200
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 503)
        self.assertLessEqual(len(err), 500)
        self.assertIn("upstream", err)
        self.assertIsNone(data)

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_2xx_non_json(self, mock_req, mock_expand):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.text = "not-json"
        mock_resp.json.side_effect = ValueError("no json")
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 204)
        self.assertEqual(err, "")
        self.assertIsNone(data)

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_error_code_non_ok(self, mock_req, mock_expand):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"errorCode":1}'
        mock_resp.json.return_value = {"errorCode": 99, "message": "nope"}
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 200)
        self.assertEqual(err, "nope")
        self.assertIsInstance(data, dict)

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_plain_dict_without_error_code(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.return_value = {"hello": "world"}
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 200)
        self.assertEqual(err, "")
        self.assertEqual(data, {"hello": "world"})

    @patch("app_saga.services.outbound_http.maybe_expand_service_discovery_url")
    @patch("app_saga.services.outbound_http.request_sync")
    def test_call_saga_endpoint_list_json_treated_as_no_dict(
        self, mock_req, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "[]"
        mock_resp.json.return_value = [1, 2]
        mock_req.return_value = mock_resp
        st, err, data = outbound_http.call_saga_endpoint(
            url="http://example.test/x",
            json_body={},
            timeout_sec=1.0,
        )
        self.assertEqual(st, 200)
        self.assertEqual(err, "")
        self.assertIsNone(data)

    def test_merge_context_from_response_noop(self):
        ctx = {"a": 1}
        outbound_http.merge_context_from_response(ctx, None)
        self.assertEqual(ctx, {"a": 1})

    def test_merge_context_from_response_merges_data_dict(self):
        ctx = {"a": 1}
        outbound_http.merge_context_from_response(
            ctx, {"errorCode": RET_OK, "data": {"b": 2, "a": 9}}
        )
        self.assertEqual(ctx["a"], 9)
        self.assertEqual(ctx["b"], 2)

    def test_loads_json_dict_invalid_raises(self):
        with self.assertRaises(ValueError):
            outbound_http.loads_json_dict("not json")

    def test_loads_json_dict_non_object_raises(self):
        with self.assertRaises(ValueError):
            outbound_http.loads_json_dict("[1]")

    def test_loads_json_dict_empty_raises(self):
        with self.assertRaises(ValueError):
            outbound_http.loads_json_dict("")

    def test_loads_json_dict_none_raises(self):
        with self.assertRaises(ValueError):
            outbound_http.loads_json_dict(None)

    def test_loads_json_dict_json_null_raises(self):
        with self.assertRaises(ValueError):
            outbound_http.loads_json_dict("null")

    def test_loads_json_dict_object_ok(self):
        self.assertEqual(outbound_http.loads_json_dict(' {"a": 1} '), {"a": 1})

    def test_dumps_json_compact(self):
        s = outbound_http.dumps_json({"a": "b"})
        self.assertEqual(s, '{"a":"b"}')
