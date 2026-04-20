"""
Functional-style tests for app_user API views: request/response and error codes.
Services are mocked so tests do not require user_rw DB or outbound HTTP.
"""
import json
import time
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_user.enums import UserStatusEnum
from app_user.utils.jwt_util import create_access_token, jwt_signing_secret
from app_user.views.user_view import (
    EventConsoleDetailView,
    EventConsoleListView,
    UserConsoleDetailView,
    UserConsoleDispositionRestoreView,
    UserConsoleListView,
    UserConsoleVerifyView,
    UserDetailView,
    UserListView,
    UserMeUpdateRequestView,
    UserMeUpdateVerifyView,
    UserJwtValidateView,
    UserMeView,
)
from common.consts.response_const import (
    RET_INVALID_PARAM,
    RET_LOGIN_REQUIRED,
    RET_OK,
    RET_RESOURCE_NOT_FOUND,
    RET_TOKEN_EXPIRED,
    RET_TOKEN_INVALID,
)
from common.utils.jwt_codec import claims_with_expiry, encode_hs256_token


def _json_response(response):
    if hasattr(response, "render"):
        response.render()
    return json.loads(response.content)


class UserViewsTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.access_token = create_access_token(user_id=7, username="me")
        patcher = patch(
            "app_user.utils.auth_context.access_token_in_use",
            return_value=True,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_jwt_validate_get_login_required(self):
        request = self.factory.get("/api/user/me/validate")
        response = UserJwtValidateView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_LOGIN_REQUIRED)

    def test_jwt_validate_get_invalid_token(self):
        request = self.factory.get(
            "/api/user/me/validate",
            HTTP_AUTHORIZATION="Bearer not-a-valid-jwt",
        )
        response = UserJwtValidateView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_TOKEN_INVALID)

    def test_jwt_validate_get_expired(self):
        past = int(time.time()) - 20_000
        claims = claims_with_expiry(
            {"type": "access", "user_id": 3, "username": "exp"},
            ttl_seconds=60,
            now=past,
        )
        token = encode_hs256_token(claims, jwt_signing_secret())
        request = self.factory.get(
            "/api/user/me/validate",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        response = UserJwtValidateView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_TOKEN_EXPIRED)

    def test_jwt_validate_get_success(self):
        request = self.factory.get(
            "/api/user/me/validate",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserJwtValidateView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["user_id"], 7)
        self.assertEqual(body["data"]["username"], "me")
        self.assertEqual(body["data"]["permissions"], [])

    def test_me_get_login_required(self):
        request = self.factory.get("/api/user/me")
        response = UserMeView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_LOGIN_REQUIRED)

    def test_me_get_token_invalid(self):
        request = self.factory.get(
            "/api/user/me",
            HTTP_AUTHORIZATION="Bearer not-a-valid-jwt",
        )
        response = UserMeView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_TOKEN_INVALID)

    @patch("app_user.views.user_view.UserService.get_me")
    def test_me_get_success(self, mock_get_me):
        mock_get_me.return_value = {"id": 7, "username": "me"}
        request = self.factory.get(
            "/api/user/me",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["username"], "me")
        mock_get_me.assert_called_once_with(user_id=7)

    @patch("app_user.views.user_view.UserService.get_me")
    def test_me_get_user_not_found(self, mock_get_me):
        mock_get_me.return_value = None
        request = self.factory.get(
            "/api/user/me",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_user.views.user_view.UserService.update_me")
    def test_me_patch_success(self, mock_update):
        mock_update.return_value = {"id": 7, "email": "n@e.w"}
        request = self.factory.patch(
            "/api/user/me",
            data={"email": "n@e.w"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["email"], "n@e.w")

    @patch("app_user.views.user_view.UserService.update_me_request_by_payload")
    def test_me_update_request_success(self, mock_req):
        mock_req.return_value = {"event_id": 99}
        request = self.factory.post(
            "/api/user/me/update/request",
            data={
                "notice_channel": "email",
                "notice_target": "x@y.z",
                "email": "x@y.z",
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeUpdateRequestView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["event_id"], 99)

    @patch("app_user.views.user_view.UserService.update_me_request_by_payload")
    def test_me_update_request_invalid_param(self, mock_req):
        mock_req.side_effect = ValueError("notice_channel must be email or sms")
        request = self.factory.post(
            "/api/user/me/update/request",
            data={"notice_channel": "fax", "notice_target": "x"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeUpdateRequestView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_INVALID_PARAM)

    @patch("app_user.views.user_view.UserService.update_me_verify_by_payload")
    def test_me_update_verify_success(self, mock_verify):
        mock_verify.return_value = {"id": 7, "username": "me"}
        request = self.factory.post(
            "/api/user/me/update/verify",
            data={"event_id": 1, "code": "123456"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeUpdateVerifyView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_verify.assert_called_once()

    @patch("app_user.views.user_view.UserService.update_me_verify_by_payload")
    def test_me_update_verify_not_found(self, mock_verify):
        mock_verify.return_value = None
        request = self.factory.post(
            "/api/user/me/update/verify",
            data={"event_id": 1, "code": "123456"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        response = UserMeUpdateVerifyView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_user.views.user_view.UserService.console_verify_user_by_code")
    def test_console_user_verify_success(self, mock_verify):
        mock_verify.return_value = {"user": {"id": 3}, "auth_status": 1}
        request = self.factory.post(
            "/api/user/console/users/3/verify",
            data={"code": "999999"},
            format="json",
        )
        response = UserConsoleVerifyView.as_view()(request, user_id=3)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["auth_status"], 1)
        mock_verify.assert_called_once_with(user_id=3, code="999999")

    @patch("app_user.views.user_view.UserService.console_update_user_by_payload")
    def test_console_user_patch_success(self, mock_update):
        mock_update.return_value = {"id": 2, "email": "p@q.r"}
        request = self.factory.patch(
            "/api/user/console/users/2",
            data={"email": "p@q.r"},
            format="json",
        )
        response = UserConsoleDetailView.as_view()(request, user_id=2)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_update.assert_called_once()

    @patch("app_user.views.user_view.UserService.list_users")
    def test_user_list_get_success(self, mock_list):
        mock_list.return_value = {
            "data": [{"id": 1}],
            "next_offset": None,
            "total_num": 1,
        }
        request = self.factory.get("/api/user/users", {"offset": 0, "limit": 10})
        response = UserListView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["total_num"], 1)
        mock_list.assert_called_once()

    @patch("app_user.views.user_view.UserService.get_me")
    def test_user_detail_get_not_found(self, mock_get):
        mock_get.return_value = None
        request = self.factory.get("/api/user/users/123")
        response = UserDetailView.as_view()(request, user_id=123)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_user.views.user_view.UserService.get_me")
    def test_user_detail_get_success(self, mock_get):
        mock_get.return_value = {"id": 5, "username": "x"}
        request = self.factory.get("/api/user/users/5")
        response = UserDetailView.as_view()(request, user_id=5)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["id"], 5)

    def test_user_detail_patch_missing_status(self):
        request = self.factory.patch("/api/user/users/1", data={}, format="json")
        response = UserDetailView.as_view()(request, user_id=1)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_INVALID_PARAM)

    def test_user_detail_patch_invalid_status(self):
        request = self.factory.patch(
            "/api/user/users/1",
            data={"status": 99},
            format="json",
        )
        response = UserDetailView.as_view()(request, user_id=1)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_INVALID_PARAM)

    @patch("app_user.views.user_view.UserService.set_status")
    def test_user_detail_patch_success(self, mock_set):
        disabled = UserStatusEnum.DISABLED.value
        mock_set.return_value = {"id": 1, "status": disabled}
        request = self.factory.patch(
            "/api/user/users/1",
            data={"status": disabled},
            format="json",
        )
        response = UserDetailView.as_view()(request, user_id=1)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_set.assert_called_once_with(user_id=1, status=disabled)

    @patch("app_user.views.user_view.AuthService.register_request_by_payload")
    def test_console_user_create_forwards_to_register_flow(self, mock_reg):
        mock_reg.return_value = {"event_id": 1}
        request = self.factory.post(
            "/api/user/console/users",
            data={"email": "c@d.e", "username": "cu", "password": "pw"},
            format="json",
        )
        response = UserConsoleListView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        mock_reg.assert_called_once()
        call_kw = mock_reg.call_args[0][0]
        self.assertEqual(call_kw["notice_channel"], "email")
        self.assertEqual(call_kw["notice_target"], "c@d.e")

    @patch("app_user.views.user_view.EventService.list_events")
    def test_console_event_list_success(self, mock_list):
        mock_list.return_value = {"data": [], "next_offset": None, "total_num": 0}
        request = self.factory.get("/api/user/console/events")
        response = EventConsoleListView.as_view()(request)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)

    @patch("app_user.views.user_view.EventService.get_event")
    def test_console_event_detail_not_found(self, mock_get):
        mock_get.return_value = None
        request = self.factory.get("/api/user/console/events/1")
        response = EventConsoleDetailView.as_view()(request, event_id=1)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_RESOURCE_NOT_FOUND)

    @patch("app_user.views.user_view.EventService.delete_event")
    def test_console_event_delete_success(self, mock_del):
        mock_del.return_value = True
        request = self.factory.delete("/api/user/console/events/9")
        response = EventConsoleDetailView.as_view()(request, event_id=9)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertTrue(body["data"]["deleted"])
        mock_del.assert_called_once_with(event_id=9)

    @patch("app_user.views.user_view.UserService.console_clear_disposition")
    def test_console_disposition_restore_success(self, mock_clear):
        mock_clear.return_value = {"id": 4, "ctrl_status": 0}
        request = self.factory.post(
            "/api/user/console/users/4/disposition/restore",
            data={},
            format="json",
        )
        response = UserConsoleDispositionRestoreView.as_view()(request, user_id=4)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_OK)
        self.assertEqual(body["data"]["ctrl_status"], 0)
        mock_clear.assert_called_once_with(user_id=4)

    @patch("app_user.views.user_view.UserService.console_clear_disposition")
    def test_console_disposition_restore_not_found(self, mock_clear):
        mock_clear.return_value = None
        request = self.factory.post(
            "/api/user/console/users/404/disposition/restore",
            data={},
            format="json",
        )
        response = UserConsoleDispositionRestoreView.as_view()(request, user_id=404)
        body = _json_response(response)
        self.assertEqual(body["errorCode"], RET_RESOURCE_NOT_FOUND)
