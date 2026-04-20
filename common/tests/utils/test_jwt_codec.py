import time

from django.test import SimpleTestCase

from common.utils.jwt_codec import claims_with_expiry, decode_hs256_token, encode_hs256_token


class JwtCodecTests(SimpleTestCase):
    def test_encode_decode_roundtrip(self):
        secret = "test-secret-key"
        now = int(time.time())
        claims = claims_with_expiry({"sub": "user1", "type": "access"}, ttl_seconds=3600, now=now)
        token = encode_hs256_token(claims, secret)
        out = decode_hs256_token(token, secret)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out.get("sub"), "user1")
        self.assertEqual(out.get("type"), "access")
        self.assertEqual(out.get("iat"), now)
        self.assertEqual(out.get("exp"), now + 3600)

    def test_decode_empty_returns_none(self):
        self.assertIsNone(decode_hs256_token("", "secret"))

    def test_decode_wrong_secret_returns_none(self):
        token = encode_hs256_token(claims_with_expiry({"a": 1}, 60, now=1), "s1")
        self.assertIsNone(decode_hs256_token(token, "s2"))

    def test_claims_with_expiry_overwrites_time_fields(self):
        c = claims_with_expiry({"iat": 1, "exp": 2, "k": "v"}, ttl_seconds=10, now=100)
        self.assertEqual(c["iat"], 100)
        self.assertEqual(c["exp"], 110)
        self.assertEqual(c["k"], "v")
