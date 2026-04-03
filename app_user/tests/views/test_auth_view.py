import json
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from app_user.views.auth_view import (
    LoginView,
    PasswordResetVerifyView,
    PasswordResetView,
    RegisterVerifyView,
    RegisterView,
)
from common.consts.response_const import (
    RET_INVALID_PARAM,
    RET_OK,
    RET_TOKEN_INVALID,
    RET_UNAUTHORIZED,
)


def _json_response(response):
    if hasattr(response, "render"):
        response.render()
    return json.loads(response.content)


class AuthViewsTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("app_user.views.auth_view.AuthService.register_request_by_payload")
    def test_register_post_success(self, mock_register):
        mock_register.return_value = {"event_id": 42}
        request = self.factory.post(
            "/api/user/register",
            data={"username": "u1", "password": "p1"},
            format="json",
        )
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["event_id"], 42)
        mock_register.assert_called_once()

    @patch("app_user.views.auth_view.AuthService.register_request_by_payload")
    def test_register_post_invalid_param(self, mock_register):
        mock_register.side_effect = ValueError("bad payload")
        request = self.factory.post("/api/user/register", data={}, format="json")
        response = RegisterView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_INVALID_PARAM)
        self.assertIn("bad payload", body["message"])

    @patch("app_user.views.auth_view.AuthService.register_verify_by_payload")
    def test_register_verify_post_success(self, mock_verify):
        mock_verify.return_value = {"user_id": 1}
        request = self.factory.post(
            "/api/user/register/verify",
            data={"code": "123456"},
            format="json",
        )
        response = RegisterVerifyView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["user_id"], 1)

    @patch("app_user.views.auth_view.AuthService.login")
    def test_login_post_success(self, mock_login):
        mock_login.return_value = {
            "access_token": "a",
            "refresh_token": "r",
            "user": {"id": 1, "username": "u"},
        }
        request = self.factory.post(
            "/api/user/login",
            data={"login_key": "u", "password": "p"},
            format="json",
        )
        response = LoginView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_login.assert_called_once_with(login_key="u", password="p")

    @patch("app_user.views.auth_view.AuthService.login")
    def test_login_post_unauthorized(self, mock_login):
        mock_login.side_effect = ValueError("invalid credentials")
        request = self.factory.post(
            "/api/user/login",
            data={"login_key": "u", "password": "wrong"},
            format="json",
        )
        response = LoginView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_UNAUTHORIZED)

    @patch("app_user.views.auth_view.AuthService.refresh")
    def test_login_put_refresh_success(self, mock_refresh):
        mock_refresh.return_value = {"access_token": "na", "refresh_token": "nr"}
        request = self.factory.put(
            "/api/user/login",
            data={"refresh_token": "old_rt"},
            format="json",
        )
        response = LoginView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_refresh.assert_called_once_with(refresh_token="old_rt")

    @patch("app_user.views.auth_view.AuthService.refresh")
    def test_login_put_refresh_invalid_token(self, mock_refresh):
        mock_refresh.side_effect = ValueError("expired")
        request = self.factory.put(
            "/api/user/login",
            data={"refresh_token": "bad"},
            format="json",
        )
        response = LoginView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_TOKEN_INVALID)

    @patch("app_user.views.auth_view.AuthService.request_password_reset_by_payload")
    def test_password_reset_post_success(self, mock_req):
        mock_req.return_value = {"ok": True}
        request = self.factory.post(
            "/api/user/reset-password",
            data={"email": "a@b.c"},
            format="json",
        )
        response = PasswordResetView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)

    @patch("app_user.views.auth_view.AuthService.verify_password_reset_by_payload")
    def test_password_reset_verify_post_invalid(self, mock_verify):
        mock_verify.side_effect = ValueError("invalid code")
        request = self.factory.post(
            "/api/user/reset-password/verify",
            data={"code": "x"},
            format="json",
        )
        response = PasswordResetVerifyView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_INVALID_PARAM)
