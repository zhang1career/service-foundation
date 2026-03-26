from unittest import TestCase
from unittest.mock import patch

from common.services.text.text_helper import TextHelper, VEC_DIM


class TestTextHelper(TestCase):
    def setUp(self):
        self.dut = TextHelper()

    @patch("common.services.text.text_helper.aibroker_embed")
    def test_find_most_similar_str(self, mock_embed):
        """Uses broker HTTP client; mock returns orthogonal-ish vectors so cosine picks match."""

        def side_effect(text, dimensions=None):
            t = (text or "").strip()
            v = [0.0] * VEC_DIM
            if "不启用" in t:
                v[0] = 1.0
            elif "启用" in t:
                v[1] = 1.0
            else:
                v[2] = 1.0
            return v

        mock_embed.side_effect = side_effect

        text_list = ["启用", "不启用"]
        match_text = "不启用"
        matched, similarity = self.dut.find_most_similar_str(text_list, match_text)
        self.assertEqual(matched, "不启用")
        self.assertGreater(similarity, 0.99)
        self.assertEqual(mock_embed.call_count, 3)
