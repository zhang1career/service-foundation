from unittest import TestCase
from unittest.mock import MagicMock

from app_aibroker.services.embedding_generation_service import INVALID_DIMENSIONS_MSG, embed_text
from common.consts.response_const import RET_AI_ERROR, RET_INVALID_PARAM


class EmbeddingGenerationServiceTest(TestCase):
    def test_invalid_dimensions_zero(self):
        reg = MagicMock()
        reg.id = 1
        data, err, code = embed_text(reg, {"input": "hello", "dimensions": 0})
        self.assertEqual(data, {})
        self.assertEqual(err, INVALID_DIMENSIONS_MSG)
        self.assertEqual(code, RET_INVALID_PARAM)

    def test_invalid_dimensions_non_numeric(self):
        reg = MagicMock()
        reg.id = 1
        data, err, code = embed_text(reg, {"input": "hello", "dimensions": "nope"})
        self.assertEqual(err, INVALID_DIMENSIONS_MSG)
        self.assertEqual(code, RET_INVALID_PARAM)

    def test_invalid_dimensions_bool(self):
        reg = MagicMock()
        reg.id = 1
        data, err, code = embed_text(reg, {"input": "hello", "dimensions": True})
        self.assertEqual(err, INVALID_DIMENSIONS_MSG)
        self.assertEqual(code, RET_INVALID_PARAM)

    def test_missing_input_returns_ai_error(self):
        reg = MagicMock()
        reg.id = 1
        data, err, code = embed_text(reg, {"dimensions": 128})
        self.assertEqual(data, {})
        self.assertIn("input", err or "")
        self.assertEqual(code, RET_AI_ERROR)
