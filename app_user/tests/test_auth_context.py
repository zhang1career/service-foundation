from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_user.services.jwt_util import create_access_token
from app_user.views.auth_context import bearer_user_id_from_request
from common.consts.response_const import RET_LOGIN_REQUIRED, RET_TOKEN_INVALID


class TestAuthContext(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_missing_authorization_returns_login_required(self):
        request = self.factory.get("/api/x")
        user_id, code, message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_LOGIN_REQUIRED)
        self.assertIn("login", message.lower())

    def test_invalid_token_returns_token_invalid(self):
        request = self.factory.get(
            "/api/x",
            HTTP_AUTHORIZATION="Bearer not-a-jwt",
        )
        user_id, code, _message = bearer_user_id_from_request(request)
        self.assertIsNone(user_id)
        self.assertEqual(code, RET_TOKEN_INVALID)

    def test_valid_access_token_returns_user_id(self):
        token = create_access_token(user_id=8, username="u8")
        request = self.factory.get(
            "/api/x",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        user_id, code, message = bearer_user_id_from_request(request)
        self.assertEqual(user_id, 8)
        self.assertEqual(code, 0)
        self.assertEqual(message, "")
