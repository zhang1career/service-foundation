from unittest import TestCase


class TestTypeUtil(TestCase):
    def test_parse_int_or_default(self):
        from common.utils.type_util import parse_int_or_default

        self.assertEqual(parse_int_or_default(None, 7), 7)
        self.assertEqual(parse_int_or_default("  ", 7), 7)
        self.assertEqual(parse_int_or_default(3, 7), 3)
        self.assertEqual(parse_int_or_default("9", 0), 9)

        with self.assertRaises(ValueError) as ctx:
            parse_int_or_default("nope", 0)
        self.assertEqual(str(ctx.exception), "invalid integer")
