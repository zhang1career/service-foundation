from django.test import SimpleTestCase

from app_user.utils.jwt_util import (
    access_expires_at_ms_from_token,
    create_access_token,
    create_refresh_token,
    decode_access_token_light,
    decode_token,
)


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

    def test_access_expires_at_ms_from_token_matches_exp_claim(self):
        token = create_access_token(user_id=1, username="u")
        ms = access_expires_at_ms_from_token(token)
        payload = decode_token(token)
        assert payload is not None
        self.assertEqual(ms, int(payload["exp"]) * 1000)

    def test_access_expires_at_ms_invalid_token_raises(self):
        with self.assertRaises(ValueError) as ctx:
            access_expires_at_ms_from_token("not-a-jwt")
        self.assertIn("exp", str(ctx.exception).lower())

    def test_decode_access_token_light_refresh_rejected(self):
        token = create_refresh_token(user_id=1, username="u")
        claims, err = decode_access_token_light(token)
        self.assertIsNone(claims)
        self.assertEqual(err, "invalid")

    def test_decode_access_token_light_success(self):
        token = create_access_token(user_id=9, username="n")
        claims, err = decode_access_token_light(token)
        self.assertIsNone(err)
        assert claims is not None
        self.assertEqual(claims.get("user_id"), 9)
        self.assertEqual(claims.get("username"), "n")

    def test_decode_access_token_light_empty_invalid(self):
        claims, err = decode_access_token_light("")
        self.assertIsNone(claims)
        self.assertEqual(err, "invalid")
