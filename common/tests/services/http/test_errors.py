from unittest import TestCase

from common.services.http.errors import HttpCallError


class HttpErrorsTest(TestCase):
    def test_http_call_error_is_runtime_error(self):
        err = HttpCallError("upstream failed")
        self.assertIsInstance(err, RuntimeError)
        self.assertEqual(str(err), "upstream failed")
