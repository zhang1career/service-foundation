from django.test import SimpleTestCase, override_settings
from rest_framework import status as http_status

from common.utils.http_util import resp_ok, resp_err, resp_exception


class TestHttpResponseUtil(SimpleTestCase):
    def test_resp_ok(self):
        response = resp_ok({"k": "v"}, status=http_status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(response.data["errorCode"], 0)
        self.assertEqual(response.data["data"], {"k": "v"})

    def test_resp_err(self):
        response = resp_err("bad request", code=100, status=http_status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["errorCode"], 100)
        self.assertEqual(response.data["message"], "bad request")
        self.assertNotIn("detail", response.data)
        self.assertNotIn("_req_id", response.data)

    def test_resp_err_detail_req_id(self):
        response = resp_err(
            "bad request",
            code=100,
            status=http_status.HTTP_400_BAD_REQUEST,
            detail="field x",
            req_id="abc",
        )
        self.assertEqual(response.data["detail"], "field x")
        self.assertEqual(response.data["_req_id"], "abc")

    @override_settings(DEBUG=False)
    def test_resp_exception_debug_false(self):
        response = resp_exception(ValueError("x"), code=1, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.status_code, http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["errorCode"], 1)
        self.assertEqual(response.data["message"], "x")
