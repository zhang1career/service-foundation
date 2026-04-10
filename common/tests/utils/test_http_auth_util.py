from types import SimpleNamespace

from django.test import SimpleTestCase

from common.utils.http_auth_util import (
    authorization_header_from_request,
    build_auth_headers,
    parse_bearer_token,
)


class ParseBearerTokenTests(SimpleTestCase):
    def test_empty_returns_none(self):
        self.assertIsNone(parse_bearer_token(""))
        self.assertIsNone(parse_bearer_token(None))

    def test_wrong_scheme_returns_none(self):
        self.assertIsNone(parse_bearer_token("Basic xxx"))

    def test_single_part_returns_none(self):
        self.assertIsNone(parse_bearer_token("Bearer"))

    def test_success_scheme_case_insensitive(self):
        self.assertEqual(parse_bearer_token("bearer abc.token"), "abc.token")


class AuthorizationHeaderFromRequestTests(SimpleTestCase):
    def test_missing_returns_empty(self):
        req = SimpleNamespace(META={})
        self.assertEqual(authorization_header_from_request(req), "")

    def test_present_returns_value(self):
        req = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer x"})
        self.assertEqual(authorization_header_from_request(req), "Bearer x")

    def test_non_str_meta_treated_as_empty(self):
        req = SimpleNamespace(META={"HTTP_AUTHORIZATION": 123})
        self.assertEqual(authorization_header_from_request(req), "")


class BuildAuthHeadersTests(SimpleTestCase):
    def test_bearer_default(self):
        h = build_auth_headers(api_key="k", auth_mode="bearer")
        self.assertEqual(h["Authorization"], "Bearer k")
        self.assertEqual(h["Content-Type"], "application/json")

    def test_empty_key_no_auth_headers(self):
        h = build_auth_headers(api_key="", auth_mode="bearer")
        self.assertNotIn("Authorization", h)
        self.assertNotIn("api-key", h)

    def test_api_key_mode(self):
        h = build_auth_headers(api_key="secret", auth_mode="api-key")
        self.assertEqual(h["api-key"], "secret")

    def test_opensearch_mode(self):
        h = build_auth_headers(api_key="osk", auth_mode="opensearch")
        self.assertEqual(h["Authorization"], "ApiKey osk")
