import json
import sys
import types
from unittest import TestCase
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory

# Avoid importing heavy OpenAI dependency chain during test collection.
if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from app_aibroker.views.embedding_view import EmbeddingCreateView
from app_aibroker.views.health_view import HealthView
from app_aibroker.views.provider_view import ProviderListCreateView
from app_aibroker.views.text_view import TextGenerateView
from common.consts.response_const import RET_AI_ERROR, RET_INVALID_PARAM, RET_OK, RET_UNAUTHORIZED


class AIBrokerViewsFunctionalTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_health_success(self):
        request = self.factory.get("/api/ai/v1/health")
        response = HealthView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["service"], "app_aibroker")

    @patch("app_aibroker.views.text_view.resolve_reg")
    def test_text_generate_unauthorized(self, resolve_reg_mock):
        resolve_reg_mock.return_value = (None, "invalid access_key")
        request = self.factory.post("/api/ai/v1/text/generate", data={"access_key": "bad"}, format="json")
        response = TextGenerateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_UNAUTHORIZED)

    @patch("app_aibroker.views.text_view.generate_text")
    @patch("app_aibroker.views.text_view.resolve_reg")
    def test_text_generate_success(self, resolve_reg_mock, generate_text_mock):
        resolve_reg_mock.return_value = ({"id": 1}, None)
        generate_text_mock.return_value = ({"text": "hello"}, None)
        request = self.factory.post(
            "/api/ai/v1/text/generate",
            data={"access_key": "k", "prompt": "hi"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="idem-1",
        )
        response = TextGenerateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["text"], "hello")

    @patch("app_aibroker.views.text_view.generate_text")
    @patch("app_aibroker.views.text_view.resolve_reg")
    def test_text_generate_multipart_rejects_files(
        self, resolve_reg_mock, generate_text_mock
    ):
        resolve_reg_mock.return_value = ({"id": 1}, None)
        generate_text_mock.return_value = ({"text": "ok"}, None)
        meta = {
            "access_key": "k",
            "template_id": 1,
            "model_id": 2,
            "variables": {},
            "temperature": 0.5,
        }
        request = self.factory.post(
            "/api/ai/v1/text/generate",
            data={
                "meta": json.dumps(meta),
                "files": SimpleUploadedFile("x.jpg", b"\xff\xd8\xff", content_type="image/jpeg"),
            },
            format="multipart",
        )
        response = TextGenerateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("files are not accepted", payload.get("message", ""))
        generate_text_mock.assert_not_called()

    @patch("app_aibroker.views.embedding_view.embed_text")
    @patch("app_aibroker.views.embedding_view.resolve_reg")
    def test_embedding_ai_error(self, resolve_reg_mock, embed_text_mock):
        resolve_reg_mock.return_value = ({"id": 2}, None)
        embed_text_mock.return_value = ({}, "provider error", RET_AI_ERROR)
        request = self.factory.post("/api/ai/v1/embeddings", data={"access_key": "k"}, format="json")
        response = EmbeddingCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_AI_ERROR)

    @patch("app_aibroker.views.embedding_view.embed_text")
    @patch("app_aibroker.views.embedding_view.resolve_reg")
    def test_embedding_invalid_dimensions_returns_invalid_param(self, resolve_reg_mock, embed_text_mock):
        resolve_reg_mock.return_value = ({"id": 2}, None)
        embed_text_mock.return_value = ({}, "dimensions must be a positive integer", RET_INVALID_PARAM)
        request = self.factory.post(
            "/api/ai/v1/embeddings",
            data={"access_key": "k", "input": "hello", "dimensions": 0},
            format="json",
        )
        response = EmbeddingCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.provider_view.ProviderService")
    def test_provider_create_invalid_payload(self, provider_service_cls):
        provider_service_cls.create_by_payload.side_effect = ValueError("name is required")
        request = self.factory.post("/api/ai/v1/providers", data={}, format="json")
        response = ProviderListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
