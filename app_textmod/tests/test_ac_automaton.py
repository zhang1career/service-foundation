from __future__ import annotations

import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from app_textmod.services.ac_automaton import build_ac_from_normalized_patterns, CompiledAutomaton, iter_ac_hits


class AcAutomatonTest(SimpleTestCase):
    def test_roundtrip_dump_load(self) -> None:
        items = [
            ("abc", 3, "abc", 1, 9, 2, 0),
            ("ab", 2, "ab", 2, 8, 1, 0),
        ]
        ac = build_ac_from_normalized_patterns(items)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.bin"
            ac.dump_path(p)
            ac2 = CompiledAutomaton.load_path(p)
        self.assertEqual(ac2.words, ac.words)

    def test_hits_overlap(self) -> None:
        ac = build_ac_from_normalized_patterns(
            [
                ("失败", 2, "失败", 10, 1, 2, 0),
                ("战败", 2, "战败", 11, 1, 2, 0),
            ]
        )
        norm = "abc战败def"
        hits = list(iter_ac_hits(ac, norm))
        self.assertTrue(any(h[2] == 1 for h in hits))
