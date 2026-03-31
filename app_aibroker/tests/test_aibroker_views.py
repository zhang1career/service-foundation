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
from app_aibroker.views.job_view import JobCreateView, JobDetailView
from app_aibroker.views.metrics_view import MetricsSummaryView
from app_aibroker.views.provider_view import (
    ModelDetailView,
    ModelListCreateView,
    ProviderDetailView,
    ProviderListCreateView,
)
from app_aibroker.views.asset_view import AssetCreateView, AssetDetailView
from app_aibroker.views.reg_view import RegDetailView, RegListCreateView
from app_aibroker.views.template_view import TemplateDetailView, TemplateListCreateView
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

    @patch("app_aibroker.views.provider_view.ProviderService")
    def test_provider_detail_get_success(self, provider_service_cls):
        provider_service_cls.get_one.return_value = {"id": 3, "name": "p"}
        request = self.factory.get("/api/ai/v1/providers/3")
        response = ProviderDetailView.as_view()(request, provider_id=3)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 3)

    @patch("app_aibroker.views.provider_view.ModelService")
    def test_model_create_invalid_payload(self, model_service_cls):
        model_service_cls.create_by_payload.side_effect = ValueError("provider_id required")
        request = self.factory.post(
            "/api/ai/v1/providers/1/models", data={"model_name": ""}, format="json"
        )
        response = ModelListCreateView.as_view()(request, provider_id=1)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.provider_view.ModelService")
    def test_model_patch_success(self, model_service_cls):
        model_service_cls.update.return_value = {"id": 9, "model_name": "new"}
        request = self.factory.patch(
            "/api/ai/v1/providers/1/models/9",
            data={"model_name": "new"},
            format="json",
        )
        response = ModelDetailView.as_view()(request, provider_id=1, model_id=9)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 9)

    @patch("app_aibroker.views.template_view.TemplateAdminService")
    def test_template_list_with_template_key_filter(self, admin_service_cls):
        admin_service_cls.list_all.return_value = [{"id": 1}]
        request = self.factory.get("/api/ai/v1/templates?template_key=t.k")
        response = TemplateListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        admin_service_cls.list_all.assert_called_once_with("t.k")
        self.assertEqual(payload["data"]["data"][0]["id"], 1)

    @patch("app_aibroker.views.template_view.TemplateAdminService")
    def test_template_detail_patch_invalid_param(self, admin_service_cls):
        admin_service_cls.update_by_payload.side_effect = ValueError("invalid template")
        request = self.factory.patch(
            "/api/ai/v1/templates/7", data={"status": 2}, format="json"
        )
        response = TemplateDetailView.as_view()(request, template_id=7)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.job_view.resolve_reg")
    def test_job_create_unauthorized(self, resolve_reg_mock):
        resolve_reg_mock.return_value = (None, "invalid access_key")
        request = self.factory.post("/api/ai/v1/jobs", data={"access_key": "bad"}, format="json")
        response = JobCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_UNAUTHORIZED)

    @patch("app_aibroker.views.job_view.resolve_reg")
    @patch("app_aibroker.views.job_view.enqueue_job")
    def test_job_create_success(self, enqueue_job_mock, resolve_reg_mock):
        resolve_reg_mock.return_value = (types.SimpleNamespace(id=11), None)
        enqueue_job_mock.return_value = {"id": 99, "status": "queued"}
        request = self.factory.post(
            "/api/ai/v1/jobs",
            data={
                "access_key": "k",
                "job_type": "text",
                "payload": {"template_id": 1},
                "callback_url": "https://example.com/cb",
            },
            format="json",
        )
        response = JobCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 99)
        enqueue_job_mock.assert_called_once_with(
            11, "text", {"template_id": 1}, "https://example.com/cb"
        )

    @patch("app_aibroker.views.job_view.resolve_reg")
    @patch("app_aibroker.views.job_view.get_job_by_id")
    def test_job_detail_not_found_when_owner_mismatch(self, get_job_by_id_mock, resolve_reg_mock):
        resolve_reg_mock.return_value = (types.SimpleNamespace(id=1), None)
        get_job_by_id_mock.return_value = types.SimpleNamespace(id=6, reg_id=2)
        request = self.factory.get("/api/ai/v1/jobs/6?access_key=k")
        response = JobDetailView.as_view()(request, job_id=6)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.asset_view.resolve_reg")
    def test_asset_create_unauthorized(self, resolve_reg_mock):
        resolve_reg_mock.return_value = (None, "invalid access_key")
        request = self.factory.post(
            "/api/ai/v1/assets",
            data={"access_key": "bad", "oss_bucket": "b", "oss_key": "k"},
            format="json",
        )
        response = AssetCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_UNAUTHORIZED)

    @patch("app_aibroker.views.asset_view.resolve_reg")
    @patch("app_aibroker.views.asset_view.AssetAdminService")
    def test_asset_create_success(self, asset_admin_cls, resolve_reg_mock):
        resolve_reg_mock.return_value = (types.SimpleNamespace(id=12), None)
        asset_admin_cls.create_for_reg.return_value = {"id": 5, "oss_bucket": "b"}
        request = self.factory.post(
            "/api/ai/v1/assets",
            data={"access_key": "k", "oss_bucket": "b", "oss_key": "path/a.png"},
            format="json",
        )
        response = AssetCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 5)
        asset_admin_cls.create_for_reg.assert_called_once_with(
            12, {"oss_bucket": "b", "oss_key": "path/a.png"}
        )

    @patch("app_aibroker.views.asset_view.resolve_reg")
    @patch("app_aibroker.views.asset_view.AssetAdminService")
    def test_asset_detail_invalid_param(self, asset_admin_cls, resolve_reg_mock):
        resolve_reg_mock.return_value = (types.SimpleNamespace(id=12), None)
        asset_admin_cls.get_one.side_effect = ValueError("asset not found")
        request = self.factory.get("/api/ai/v1/assets/5?access_key=k")
        response = AssetDetailView.as_view()(request, asset_id=5)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.reg_view.RegService")
    def test_reg_list_success(self, reg_service_cls):
        reg_service_cls.list_all.return_value = [{"id": 1, "name": "demo"}]
        request = self.factory.get("/api/ai/v1/regs")
        response = RegListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["data"][0]["id"], 1)

    @patch("app_aibroker.views.reg_view.RegService")
    def test_reg_create_invalid_payload(self, reg_service_cls):
        reg_service_cls.create_by_payload.side_effect = ValueError("name is required")
        request = self.factory.post("/api/ai/v1/regs", data={}, format="json")
        response = RegListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_aibroker.views.reg_view.RegService")
    def test_reg_delete_success(self, reg_service_cls):
        reg_service_cls.delete.return_value = True
        request = self.factory.delete("/api/ai/v1/regs/8")
        response = RegDetailView.as_view()(request, reg_id=8)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertTrue(payload["data"]["deleted"])

    @patch("app_aibroker.views.metrics_view.resolve_reg")
    def test_metrics_summary_unauthorized(self, resolve_reg_mock):
        resolve_reg_mock.return_value = (None, "invalid access_key")
        request = self.factory.get("/api/ai/v1/metrics/summary?access_key=bad")
        response = MetricsSummaryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_UNAUTHORIZED)

    @patch("app_aibroker.views.metrics_view.resolve_reg")
    @patch("app_aibroker.views.metrics_view.summary_since")
    def test_metrics_summary_success_with_window_ms(self, summary_since_mock, resolve_reg_mock):
        resolve_reg_mock.return_value = (types.SimpleNamespace(id=3), None)
        summary_since_mock.return_value = {"calls": 10, "success": 9}
        request = self.factory.get("/api/ai/v1/metrics/summary?access_key=k&window_ms=60000")
        response = MetricsSummaryView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["calls"], 10)
        summary_since_mock.assert_called_once_with(reg_id=3, window_ms=60000)
