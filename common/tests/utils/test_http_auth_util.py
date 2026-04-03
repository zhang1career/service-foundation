from types import SimpleNamespace

from django.test import SimpleTestCase

from common.utils.http_auth_util import authorization_header_from_request, parse_bearer_token


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
