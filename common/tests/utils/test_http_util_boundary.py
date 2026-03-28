from unittest import TestCase
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status as http_status

from common.consts.response_const import RET_INVALID_PARAM, RET_UNKNOWN
from common.exceptions.base_exception import UncheckedException
from common.utils.http_util import drf_unified_exception_handler, resolve_request_id, with_type


class DummyRequest:
    def __init__(self, meta=None, path="/api/x"):
        self.META = meta or {}
        self.path = path
        self.request_id = None


class HttpUtilBoundaryTest(TestCase):
    def test_with_type_nested_and_literals(self):
        data = {"a": "001", "b": "TRUE", "c": ["false", "1.2", "x%20y"]}
        result = with_type(data)
        self.assertEqual(result["a"], 1)
        self.assertTrue(result["b"])
        self.assertEqual(result["c"][0], False)
        self.assertEqual(result["c"][1], "1.2")
        self.assertEqual(result["c"][2], "x y")

    def test_resolve_request_id_blank_or_missing(self):
        req = DummyRequest(meta={"HTTP_X_REQUEST_ID": " "})
        rid = resolve_request_id(req)
        self.assertEqual(len(rid), 16)
        self.assertEqual(len(resolve_request_id(None)), 16)

    def test_drf_handler_value_error_maps_to_invalid_param(self):
        req = DummyRequest()
        resp = drf_unified_exception_handler(ValueError("bad input"), {"request": req})
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["errorCode"], RET_INVALID_PARAM)

    @override_settings(DEBUG=False)
    @patch("common.utils.http_util.drf_exception_handler", return_value=None)
    def test_drf_handler_unknown_exception(self, _drf_handler_mock):
        req = DummyRequest()
        resp = drf_unified_exception_handler(RuntimeError("oops"), {"request": req})
        self.assertEqual(resp.status_code, http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.data["errorCode"], RET_UNKNOWN)

    @override_settings(DEBUG=False)
    def test_drf_handler_unchecked_exception_hides_detail(self):
        req = DummyRequest()
        exc = UncheckedException(ret_code=1234, detail="internal detail")
        resp = drf_unified_exception_handler(exc, {"request": req})
        self.assertEqual(resp.status_code, http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertNotIn("detail", resp.data)
