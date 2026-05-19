from __future__ import annotations

from django.test import SimpleTestCase

from app_textmod.services.text_normalizer import normalize_for_match


class TextNormalizerTest(SimpleTestCase):
    def test_fullwidth_ascii_maps(self) -> None:
        norm, mp = normalize_for_match("ＡＢＣ", strip_edges=False)
        self.assertEqual(norm, "abc")
        self.assertEqual(mp, [0, 1, 2])

    def test_strip_edges_keeps_mapping(self) -> None:
        norm, mp = normalize_for_match("  hello  ")
        self.assertEqual(norm, "hello")
        self.assertEqual(mp, [2, 3, 4, 5, 6])

    def test_zero_width_dropped(self) -> None:
        norm, mp = normalize_for_match("a\u200bb")
        self.assertEqual(norm, "ab")
        self.assertEqual(mp, [0, 2])
