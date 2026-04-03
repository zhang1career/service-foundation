from django.test import SimpleTestCase

from app_user.services.jwt_util import create_access_token, decode_token


class TestJwtUtil(SimpleTestCase):
    def test_decode_token_empty_returns_none(self):
        self.assertIsNone(decode_token(""))

    def test_create_and_decode_access_roundtrip(self):
        token = create_access_token(user_id=3, username="u3")
        payload = decode_token(token)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.get("type"), "access")
        self.assertEqual(payload.get("user_id"), 3)
        self.assertEqual(payload.get("username"), "u3")
