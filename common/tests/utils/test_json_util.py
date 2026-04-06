from unittest import TestCase


class TestJsonDecode(TestCase):
    def test_none_returns_none(self):
        from common.utils.json_util import json_decode

        self.assertIsNone(json_decode(None))

    def test_valid_object_and_array(self):
        from common.utils.json_util import json_decode

        self.assertEqual(json_decode('{"a": 1}'), {"a": 1})
        self.assertEqual(json_decode("[1,2]"), [1, 2])
        self.assertEqual(json_decode('"x"'), "x")
        self.assertIsNone(json_decode("null"))

    def test_strips_outer_whitespace(self):
        from common.utils.json_util import json_decode

        self.assertEqual(json_decode('  {"k": true} \n'), {"k": True})

    def test_non_str_raises(self):
        from common.utils.json_util import json_decode

        with self.assertRaises(TypeError):
            json_decode(123)
        with self.assertRaises(TypeError):
            json_decode(b"{}")

    def test_empty_or_whitespace_only_raises(self):
        from common.utils.json_util import json_decode

        with self.assertRaises(ValueError) as ctx:
            json_decode("")
        self.assertIn("empty", str(ctx.exception))

        with self.assertRaises(ValueError):
            json_decode("   \n\t  ")

    def test_invalid_json_raises_value_error(self):
        from common.utils.json_util import json_decode

        with self.assertRaises(ValueError) as ctx:
            json_decode("{")
        self.assertIn("invalid JSON", str(ctx.exception))
        self.assertIsNotNone(ctx.exception.__cause__)


class TestJsonDecodeFromBytes(TestCase):
    def test_object_ok(self):
        from common.utils.json_util import json_decode_from_bytes

        self.assertEqual(json_decode_from_bytes(b'{"a":1}'), {"a": 1})

    def test_none_returns_none(self):
        from common.utils.json_util import json_decode_from_bytes

        self.assertIsNone(json_decode_from_bytes(None))

    def test_non_bytes_raises(self):
        from common.utils.json_util import json_decode_from_bytes

        with self.assertRaises(TypeError):
            json_decode_from_bytes("{}")

    def test_array_ok(self):
        from common.utils.json_util import json_decode_from_bytes

        self.assertEqual(json_decode_from_bytes(b"[1,2]"), [1, 2])

    def test_non_object_array_returns_none(self):
        from common.utils.json_util import json_decode_from_bytes

        self.assertIsNone(json_decode_from_bytes(b'"s"'))
        self.assertIsNone(json_decode_from_bytes(b"null"))
        self.assertIsNone(json_decode_from_bytes(b"true"))

    def test_invalid_utf8_returns_none(self):
        from common.utils.json_util import json_decode_from_bytes

        self.assertIsNone(json_decode_from_bytes(b"\xff"))

    def test_invalid_json_logs_warning(self):
        from common.utils.json_util import json_decode_from_bytes

        with self.assertLogs("common.utils.json_util", level="WARNING") as cm:
            self.assertIsNone(json_decode_from_bytes(b"not json"))
        self.assertTrue(any("json_decode failed" in r.getMessage() for r in cm.records))
