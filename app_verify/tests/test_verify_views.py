import json
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory
from unittest.mock import MagicMock, patch

from app_verify.services.verify_service import VerifyService
from app_verify.views.reg_view import RegDetailView, RegListCreateView
from app_verify.views.verify_view import VerifyCheckView, VerifyRequestView
from common.consts.response_const import RET_INVALID_PARAM, RET_OK


class VerifyViewsFunctionalTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_verify.views.reg_view.RegService")
    def test_reg_list_success(self, reg_service_cls):
        reg_service_cls.list_all.return_value = [{"id": 1, "name": "demo"}]
        request = self.factory.get("/api/verify/regs")
        response = RegListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["data"][0]["name"], "demo")

    @patch("app_verify.views.reg_view.RegService")
    def test_reg_create_invalid_payload(self, reg_service_cls):
        reg_service_cls.create_by_payload.side_effect = ValueError("name is required")
        request = self.factory.post("/api/verify/regs", data={}, format="json")
        response = RegListCreateView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("required", payload["message"])

    @patch("app_verify.views.reg_view.RegService")
    def test_reg_detail_get_success(self, reg_service_cls):
        reg_service_cls.get_one.return_value = {"id": 2, "name": "r2"}
        request = self.factory.get("/api/verify/regs/2")
        response = RegDetailView.as_view()(request, reg_id=2)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["id"], 2)

    @patch("app_verify.views.verify_view.VerifyService")
    def test_verify_request_and_check_success(self, verify_service_cls):
        verify_service_cls.request_code_by_payload.return_value = {"code_id": 100, "code": "123456"}
        request = self.factory.post(
            "/api/verify/request",
            data={"level": 1, "access_key": "k", "ref_id": 9},
            format="json",
        )
        response = VerifyRequestView.as_view()(request)
        response.render()
        request_payload = json.loads(response.content)
        self.assertEqual(request_payload["errorCode"], RET_OK)
        self.assertEqual(request_payload["data"]["code_id"], 100)

        verify_service_cls.verify_code_by_payload.return_value = {"verified": True}
        check_request = self.factory.post(
            "/api/verify/check",
            data={"code_id": 100, "code": "123456", "access_key": "k"},
            format="json",
        )
        check_response = VerifyCheckView.as_view()(check_request)
        check_response.render()
        check_payload = json.loads(check_response.content)
        self.assertEqual(check_payload["errorCode"], RET_OK)
        self.assertTrue(check_payload["data"]["verified"])

    @patch("app_verify.views.verify_view.VerifyService")
    def test_verify_check_invalid_payload(self, verify_service_cls):
        verify_service_cls.verify_code_by_payload.side_effect = ValueError("invalid or expired verify code")
        request = self.factory.post("/api/verify/check", data={}, format="json")
        response = VerifyCheckView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_verify.views.reg_view.RegService")
    def test_reg_detail_patch_success(self, reg_service_cls):
        reg_service_cls.update_by_payload.return_value = {"id": 2, "name": "changed"}
        request = self.factory.patch("/api/verify/regs/2", data={"name": "changed"}, format="json")
        response = RegDetailView.as_view()(request, reg_id=2)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_OK)
        self.assertEqual(payload["data"]["name"], "changed")

    @patch("app_verify.views.reg_view.RegService")
    def test_reg_detail_delete_invalid_payload(self, reg_service_cls):
        reg_service_cls.delete.side_effect = ValueError("reg not found")
        request = self.factory.delete("/api/verify/regs/999")
        response = RegDetailView.as_view()(request, reg_id=999)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)
        self.assertIn("not found", payload["message"])

    @patch("app_verify.views.verify_view.VerifyService")
    def test_verify_request_invalid_payload(self, verify_service_cls):
        verify_service_cls.request_code_by_payload.side_effect = ValueError("level must be int")
        request = self.factory.post("/api/verify/request", data={"level": "x"}, format="json")
        response = VerifyRequestView.as_view()(request)
        response.render()
        payload = json.loads(response.content)
        self.assertEqual(payload["errorCode"], RET_INVALID_PARAM)

    @patch("app_verify.services.verify_service.VerifyService._create_code_for_reg")
    @patch("app_verify.services.verify_service.get_reg_by_id")
    def test_issue_code_for_reg_id_success(self, get_reg, create_for_reg):
        reg = MagicMock()
        reg.id = 3
        reg.status = 1
        get_reg.return_value = reg
        create_for_reg.return_value = {"code_id": 42, "code": "123456", "reg_id": 3}
        out = VerifyService.issue_code_for_reg_id(3, 2, 99)
        self.assertEqual(out["code_id"], 42)
        create_for_reg.assert_called_once()
        self.assertEqual(create_for_reg.call_args[0][0], reg)
        self.assertEqual(create_for_reg.call_args[0][1], 2)
        self.assertEqual(create_for_reg.call_args[0][2], 99)

    @patch("app_verify.services.verify_service.get_reg_by_id")
    def test_issue_code_for_reg_id_missing_reg(self, get_reg):
        get_reg.return_value = None
        with self.assertRaises(ValueError):
            VerifyService.issue_code_for_reg_id(1, 0, 0)
