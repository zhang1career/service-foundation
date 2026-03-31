from unittest import TestCase
from unittest.mock import MagicMock, patch

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
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

    @patch("app_aibroker.services.embedding_generation_service.create_call_log")
    @patch("app_aibroker.services.embedding_generation_service.create_embedding")
    @patch("app_aibroker.services.embedding_generation_service.default_embedding_model")
    def test_embed_text_success_default_model(self, default_model_mock, create_embedding_mock, _log_mock):
        reg = MagicMock()
        reg.id = 1
        provider = MagicMock(id=10, status=1)
        model = MagicMock(id=20, status=1, capability=ModelCapabilityEnum.EMBEDDING, param_specs="")
        default_model_mock.return_value = (provider, model)
        create_embedding_mock.return_value = [0.1, 0.2, 0.3]

        data, err, code = embed_text(reg, {"input": " hello ", "dimensions": "3"})

        self.assertIsNone(err)
        self.assertIsNone(code)
        self.assertEqual(data["provider_id"], 10)
        self.assertEqual(data["model_id"], 20)
        self.assertEqual(data["dimensions"], 3)

    @patch("app_aibroker.services.embedding_generation_service.get_provider_by_id")
    @patch("app_aibroker.services.embedding_generation_service.get_model_by_id")
    def test_embed_text_rejects_non_embedding_model(self, get_model_mock, _get_provider_mock):
        reg = MagicMock()
        reg.id = 1
        model = MagicMock(status=1, capability=ModelCapabilityEnum.CHAT, provider_id=9)
        get_model_mock.return_value = model

        data, err, code = embed_text(reg, {"input": "ok", "model_id": 5})

        self.assertEqual(data, {})
        self.assertIn("not an embedding model", err or "")
        self.assertEqual(code, RET_AI_ERROR)
