import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch

if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from app_aibroker.services.llm_client_service import chat_completion, create_embedding
from common.enums.aigc_invoke_op_enum import AigcInvokeOp


class LlmClientServiceTest(TestCase):
    @patch("app_aibroker.services.llm_client_service.AigcAPI")
    def test_chat_completion_passes_body_and_model_added_by_aigc(self, api_cls_mock):
        provider = MagicMock(
            base_url="https://aib.example.com",
            api_key="ak",
            url_path="/v1/chat/completions",
        )
        model = MagicMock(model_name="gpt-4o-mini", capability=0)
        api_mock = api_cls_mock.return_value
        api_mock.invoke.return_value = "ok"

        body = {"messages": [{"role": "user", "content": "hello"}], "temperature": 0.2}
        out = chat_completion(provider, model, body)

        self.assertEqual(out, "ok")
        api_cls_mock.assert_called_once_with(
            base_url="https://aib.example.com",
            api_key="ak",
        )
        api_mock.invoke.assert_called_once_with(
            "/v1/chat/completions",
            AigcInvokeOp.CHAT,
            "gpt-4o-mini",
            body,
        )

    @patch("app_aibroker.services.llm_client_service.AigcAPI")
    def test_create_embedding_passes_body(self, api_cls_mock):
        provider = MagicMock(
            base_url="https://aib.example.com",
            api_key="ak",
            url_path="/v1/embeddings",
        )
        model = MagicMock(model_name="text-embedding-3-small", capability=3)
        api_mock = api_cls_mock.return_value
        api_mock.invoke.return_value = [1.0, 2.0]

        body = {"input": "hello", "encoding_format": "float", "dimensions": 384}
        vec = create_embedding(provider, model, body)

        self.assertEqual(vec, [1.0, 2.0])
        api_cls_mock.assert_called_once_with(
            base_url="https://aib.example.com",
            api_key="ak",
        )
        api_mock.invoke.assert_called_once_with(
            "/v1/embeddings",
            AigcInvokeOp.EMBEDDING,
            "text-embedding-3-small",
            body,
        )
