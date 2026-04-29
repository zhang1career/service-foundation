from unittest import TestCase

from django.http import HttpRequest


class TestParseXRequestIdInt64(TestCase):
    def test_parses_decimal_int64(self):
        from common.utils.http_util import parse_x_request_id_int64

        r = HttpRequest()
        r.META["HTTP_X_REQUEST_ID"] = "  9223372036854775807 "
        self.assertEqual(parse_x_request_id_int64(r), 9223372036854775807)

    def test_missing_raises(self):
        from common.utils.http_util import parse_x_request_id_int64

        r = HttpRequest()
        with self.assertRaises(ValueError) as ctx:
            parse_x_request_id_int64(r)
        self.assertIn("required", str(ctx.exception).lower())


class TestParseHttpTarget(TestCase):
    def test_https_default_port_and_tls(self):
        from common.utils.http_util import parse_http_target

        h, p, tls = parse_http_target("https://api.example.com")
        self.assertEqual(h, "api.example.com")
        self.assertEqual(p, 443)
        self.assertTrue(tls)

    def test_http_default_port_no_tls(self):
        from common.utils.http_util import parse_http_target

        h, p, tls = parse_http_target("http://api.example.com")
        self.assertEqual(h, "api.example.com")
        self.assertEqual(p, 80)
        self.assertFalse(tls)

    def test_schemeless_defaults_to_https(self):
        from common.utils.http_util import parse_http_target

        h, p, tls = parse_http_target("api.example.com")
        self.assertEqual(h, "api.example.com")
        self.assertEqual(p, 443)
        self.assertTrue(tls)

    def test_explicit_ports(self):
        from common.utils.http_util import parse_http_target

        h, p, tls = parse_http_target("https://h.example:8443")
        self.assertEqual(h, "h.example")
        self.assertEqual(p, 8443)
        self.assertTrue(tls)

        h2, p2, tls2 = parse_http_target("http://h.example:8080")
        self.assertEqual(h2, "h.example")
        self.assertEqual(p2, 8080)
        self.assertFalse(tls2)

    def test_strips_whitespace(self):
        from common.utils.http_util import parse_http_target

        h, p, tls = parse_http_target("  https://x.test/path  ")
        self.assertEqual(h, "x.test")
        self.assertEqual(p, 443)
        self.assertTrue(tls)

    def test_empty_raises(self):
        from common.utils.http_util import parse_http_target

        with self.assertRaises(RuntimeError) as ctx:
            parse_http_target("")
        self.assertIn("required", str(ctx.exception).lower())

        with self.assertRaises(RuntimeError):
            parse_http_target("   ")

    def test_invalid_no_host_raises(self):
        from common.utils.http_util import parse_http_target

        with self.assertRaises(RuntimeError) as ctx:
            parse_http_target("https://")
        self.assertIn("invalid", str(ctx.exception).lower())


class TestNormalizeHttpPath(TestCase):
    def test_keeps_absolute_path(self):
        from common.utils.http_util import normalize_http_path

        self.assertEqual(normalize_http_path("/v1/chat/completions"), "/v1/chat/completions")

    def test_adds_leading_slash(self):
        from common.utils.http_util import normalize_http_path

        self.assertEqual(normalize_http_path("v1/embeddings"), "/v1/embeddings")

    def test_strips_whitespace(self):
        from common.utils.http_util import normalize_http_path

        self.assertEqual(normalize_http_path("  /x/y  "), "/x/y")
        self.assertEqual(normalize_http_path("  api  "), "/api")

    def test_empty_raises(self):
        from common.utils.http_util import normalize_http_path

        with self.assertRaises(RuntimeError) as ctx:
            normalize_http_path("")
        self.assertIn("empty", str(ctx.exception).lower())

        with self.assertRaises(RuntimeError):
            normalize_http_path("   ")


class TestHttpOriginUrl(TestCase):
    def test_default_ports_omit_colon(self):
        from common.utils.http_util import http_origin_url

        self.assertEqual(http_origin_url("api.example.com", 443, True), "https://api.example.com")
        self.assertEqual(http_origin_url("api.example.com", 80, False), "http://api.example.com")

    def test_non_default_port_in_netloc(self):
        from common.utils.http_util import http_origin_url

        self.assertEqual(http_origin_url("h.test", 8443, True), "https://h.test:8443")


class _DummyRequest:
    def __init__(self, data_marker=None, post=None, with_data=True):
        self.POST = post if post is not None else {}
        if with_data:
            self.data = data_marker


class TestPostPayload(TestCase):
    def test_prefers_drf_data_when_present(self):
        from common.utils.http_util import post_payload

        req = _DummyRequest(data_marker={"a": 1}, post={"b": 2}, with_data=True)
        payload = post_payload(req)
        self.assertEqual(payload, {"a": 1})

    def test_falls_back_to_post_when_data_missing(self):
        from common.utils.http_util import post_payload

        req = _DummyRequest(post={"x": "y"}, with_data=False)
        payload = post_payload(req)
        self.assertEqual(payload, {"x": "y"})

    def test_returns_none_when_data_exists_but_none(self):
        from common.utils.http_util import post_payload

        req = _DummyRequest(data_marker=None, post={"x": "y"}, with_data=True)
        payload = post_payload(req)
        self.assertIsNone(payload)


class Test(TestCase):

    def setUp(self):
        pass

    def test_with_type(self):
        # lazy load
        from common.utils.http_util import with_type

        # normal case
        origin_data = {
            "id": "1",
            "name": "a",
            "age": 18,
            "is_active": "true",
            "children": [
                {
                    "id": "2",
                    "name": "b",
                    "is_active": "false"
                }
            ],
            "is_deleted": None,
            "is_deleted2": "null",
        }
        expected_result = {
            "id": 1,
            "name": "a",
            "age": 18,
            "is_active": True,
            "children": [
                {
                    "id": 2,
                    "name": "b",
                    "is_active": False
                }
            ],
            "is_deleted": None,
            "is_deleted2": "null"
        }
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)

        # empty case
        origin_data = {}
        expected_result = {}
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)

        # None case
        origin_data = None
        expected_result = None
        actual_result = with_type(origin_data)
        self.assertEqual(expected_result, actual_result)