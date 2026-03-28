import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch

if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from app_aibroker.services.llm_client_service import chat_completion, create_embedding


class LlmClientServiceTest(TestCase):
    @patch("app_aibroker.services.llm_client_service.AigcBestAPI")
    def test_chat_completion_calls_aigcbest_api_chat(self, api_cls_mock):
        provider = MagicMock(base_url="https://aib.example.com", api_key="ak")
        model = MagicMock(model_name="gpt-4o-mini")
        api_mock = api_cls_mock.return_value
        api_mock.chat.return_value = "ok"

        out = chat_completion(provider, model, "hello", temperature=0.2)

        self.assertEqual(out, "ok")
        api_cls_mock.assert_called_once_with(
            "gpt-4o-mini",
            base_url="https://aib.example.com",
            api_key="ak",
        )
        api_mock.chat.assert_called_once_with("hello", temperature=0.2)

    @patch("app_aibroker.services.llm_client_service.AigcBestAPI")
    def test_create_embedding_calls_aigcbest_api_embed(self, api_cls_mock):
        provider = MagicMock(base_url="https://aib.example.com", api_key="ak")
        model = MagicMock(model_name="text-embedding-3-small")
        api_mock = api_cls_mock.return_value
        api_mock.embed.return_value = [1.0, 2.0]

        vec = create_embedding(provider, model, "hello", dimensions=384)

        self.assertEqual(vec, [1.0, 2.0])
        api_cls_mock.assert_called_once_with(
            "text-embedding-3-small",
            base_url="https://aib.example.com",
            api_key="ak",
        )
        api_mock.embed.assert_called_once_with("hello", dimensions=384)
