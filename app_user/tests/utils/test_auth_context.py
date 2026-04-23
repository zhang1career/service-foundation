from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_user.utils.jwt_util import create_access_token
from app_user.utils.auth_context import bearer_user_id_from_request
from common.consts.response_const import RET_LOGIN_REQUIRED, RET_TOKEN_INVALID, RET_TOKEN_REVOKED


class TestAuthContext(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_missing_authorization_returns_login_required(self):
        request = self.factory.get("/api/x")
        user_id, code, message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_LOGIN_REQUIRED)
        self.assertIn("login", message.lower())

    def test_authorization_bearer_ignored_login_required(self):
        request = self.factory.get(
            "/api/x",
            HTTP_AUTHORIZATION="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.e30",
        )
        user_id, code, _message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_LOGIN_REQUIRED)

    def test_invalid_token_returns_token_invalid(self):
        request = self.factory.get(
            "/api/x",
            HTTP_X_USER_ACCESS_TOKEN="not-a-jwt",
        )
        user_id, code, _message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_TOKEN_INVALID)

    @patch("app_user.utils.auth_context.access_token_in_use", return_value=True)
    def test_valid_access_token_returns_user_id(self, _mock_in_use):
        token = create_access_token(user_id=8, username="u8")
        request = self.factory.get(
            "/api/x",
            HTTP_X_USER_ACCESS_TOKEN=token,
        )
        user_id, code, message = bearer_user_id_from_request(request)
        self.assertEqual(user_id, 8)
        self.assertEqual(code, 0)
        self.assertEqual(message, "")

    @patch("app_user.utils.auth_context.access_token_in_use", return_value=False)
    def test_access_token_not_in_database_returns_revoked(self, _mock_in_use):
        token = create_access_token(user_id=8, username="u8")
        request = self.factory.get(
            "/api/x",
            HTTP_X_USER_ACCESS_TOKEN=token,
        )
        user_id, code, _message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_TOKEN_REVOKED)
