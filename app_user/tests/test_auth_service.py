from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.hashers import make_password
from django.test import SimpleTestCase

from app_user.enums import UserStatusEnum
from app_user.services.auth_service import AuthService
from app_user.services.jwt_util import create_refresh_token, decode_token


def _login_user_stub(**kwargs):
    base = dict(
        id=1,
        phone="",
        avatar="",
        ext="{}",
        auth_status=0,
        ct=0,
        ut=0,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestAuthService(SimpleTestCase):
    """Login paths call get_user_by_login; mock repo like app_aibroker view tests."""

    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login(self, mock_get):
        mock_get.return_value = _login_user_stub(
            id=1,
            username="user1",
            email="user1@example.com",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("pass1234"),
        )
        logged_in = AuthService.login(login_key="user1", password="pass1234")
        self.assertIn("access_token", logged_in)
        self.assertEqual(logged_in["user"]["username"], "user1")
        mock_get.assert_called_once_with("user1")

    def test_login_empty_credentials_raises(self):
        with self.assertRaises(ValueError) as ctx:
            AuthService.login(login_key="", password="x")
        self.assertIn("required", str(ctx.exception).lower())

    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_wrong_password_raises(self, mock_get):
        mock_get.return_value = _login_user_stub(
            id=2,
            username="user2",
            email="user2@example.com",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("secret"),
        )
        with self.assertRaises(ValueError) as ctx:
            AuthService.login(login_key="user2", password="wrong")
        self.assertIn("invalid", str(ctx.exception).lower())


class TestAuthServicePasswordResetValidation(SimpleTestCase):
    def test_request_password_reset_invalid_channel_raises(self):
        with self.assertRaises(ValueError) as ctx:
            AuthService._request_password_reset(channel="fax", target="a@b.c")
        self.assertIn("email", str(ctx.exception).lower())

    def test_request_password_reset_empty_target_raises(self):
        with self.assertRaises(ValueError) as ctx:
            AuthService._request_password_reset(channel="email", target="  ")
        self.assertIn("target", str(ctx.exception).lower())


class TestAuthServiceRefresh(SimpleTestCase):
    """No DB: refresh only uses JWT crypto + settings secret."""

    def test_refresh_returns_access_and_refresh_tokens(self):
        rt = create_refresh_token(user_id=99, username="token_user")
        out = AuthService.refresh(refresh_token=rt)
        self.assertIn("access_token", out)
        self.assertIn("refresh_token", out)
        acc = decode_token(out["access_token"])
        self.assertEqual(acc.get("type"), "access")
        self.assertEqual(acc.get("user_id"), 99)
        ref = decode_token(out["refresh_token"])
        self.assertEqual(ref.get("type"), "refresh")
        self.assertEqual(ref.get("user_id"), 99)

    @patch("app_user.services.auth_service.decode_token")
    def test_refresh_rejects_non_refresh_type(self, mock_decode):
        mock_decode.return_value = {"type": "access", "user_id": 1, "username": "u"}
        with self.assertRaises(ValueError) as ctx:
            AuthService.refresh(refresh_token="any")
        self.assertIn("refresh", str(ctx.exception).lower())

    @patch("app_user.services.auth_service.decode_token")
    def test_refresh_rejects_missing_user_id(self, mock_decode):
        mock_decode.return_value = {"type": "refresh", "username": "u"}
        with self.assertRaises(ValueError) as ctx:
            AuthService.refresh(refresh_token="any")
        self.assertIn("payload", str(ctx.exception).lower())

    def test_refresh_rejects_garbage_token(self):
        with self.assertRaises(ValueError):
            AuthService.refresh(refresh_token="not.a.jwt")


class TestAuthServiceRequestPasswordReset(SimpleTestCase):
    @patch("app_user.services.auth_service.AuthService._request_password_reset")
    def test_request_password_reset_by_payload_strips_and_delegates(self, mock_inner):
        mock_inner.return_value = {"sent": True}
        out = AuthService.request_password_reset_by_payload(
            {"notice_channel": "  email  ", "notice_target": "  a@b.c  "},
        )
        self.assertEqual(out, {"sent": True})
        mock_inner.assert_called_once_with(channel="email", target="a@b.c")


class TestAuthServiceRequestPasswordResetBranches(SimpleTestCase):
    @patch("app_user.services.auth_service.create_verify_event_and_send_notice")
    @patch("app_user.services.auth_service.cancel_pending_events_by_notice")
    @patch("app_user.services.auth_service.get_user_by_email")
    def test_user_not_found_returns_sent_only(
        self, mock_get_email, mock_cancel, mock_create,
    ):
        mock_get_email.return_value = None
        out = AuthService._request_password_reset(channel="email", target="x@y.z")
        self.assertEqual(out, {"sent": True})
        mock_cancel.assert_not_called()
        mock_create.assert_not_called()

    @patch("app_user.services.auth_service.create_verify_event_and_send_notice")
    @patch("app_user.services.auth_service.cancel_pending_events_by_notice")
    @patch("app_user.services.auth_service.get_user_by_email")
    def test_user_found_creates_event(
        self, mock_get_email, mock_cancel, mock_create,
    ):
        u = _login_user_stub(
            id=3,
            username="u",
            email="x@y.z",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("p"),
        )
        mock_get_email.return_value = u
        mock_create.return_value = SimpleNamespace(id=100)
        out = AuthService._request_password_reset(channel="email", target="x@y.z")
        self.assertEqual(out, {"sent": True, "event_id": 100})
        mock_cancel.assert_called_once()
        mock_create.assert_called_once()


class TestAuthServiceVerifyPasswordReset(SimpleTestCase):
    @patch("app_user.services.auth_service.update_event_status")
    @patch("app_user.services.auth_service.update_user_password")
    @patch("app_user.services.auth_service.post_verify_check")
    @patch("app_user.services.auth_service.load_verify_notice_access_keys")
    @patch("app_user.services.auth_service.get_user_by_id")
    @patch("app_user.services.auth_service.get_event_by_id")
    def test_verify_success(
        self, mock_ge, mock_gu, mock_keys, mock_post, mock_upd_pw, mock_upd_ev,
    ):
        from app_user.enums import EventBizTypeEnum, EventStatusEnum

        ev = SimpleNamespace(
            id=7,
            biz_type=EventBizTypeEnum.PASSWORD_RESET,
            status=EventStatusEnum.PENDING_VERIFY.value,
            verify_code_id=55,
            payload_json='{"user_id": 3}',
        )
        mock_ge.return_value = ev
        mock_gu.return_value = _login_user_stub(
            id=3,
            username="u",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("old"),
        )
        mock_keys.return_value = ("vk", "nk")
        mock_post.return_value = {"errorCode": 0}
        ok = AuthService._verify_password_reset(
            event_id=7,
            code="999",
            new_password="newpass1",
        )
        self.assertTrue(ok)
        mock_upd_pw.assert_called_once()
        mock_upd_ev.assert_called_once()

    def test_verify_missing_fields_raises(self):
        with self.assertRaises(ValueError):
            AuthService._verify_password_reset(event_id=0, code="c", new_password="n")
        with self.assertRaises(ValueError):
            AuthService._verify_password_reset(event_id=1, code="", new_password="n")
        with self.assertRaises(ValueError):
            AuthService._verify_password_reset(event_id=1, code="c", new_password="")


class TestAuthServiceRegister(SimpleTestCase):
    @patch("app_user.services.auth_service.create_verify_event_and_send_notice")
    @patch("app_user.services.auth_service.upload_avatar")
    @patch("app_user.services.auth_service.get_user_by_phone")
    @patch("app_user.services.auth_service.get_user_by_email")
    @patch("app_user.services.auth_service.get_user_by_username")
    def test_register_request_success(
        self, mock_u, mock_e, mock_p, mock_av, mock_create,
    ):
        mock_u.return_value = None
        mock_e.return_value = None
        mock_p.return_value = None
        mock_av.return_value = ""
        mock_create.return_value = SimpleNamespace(id=200)
        payload = {
            "username": "newu",
            "password": "secret12",
            "email": "",
            "phone": "",
            "notice_channel": "email",
            "notice_target": "newu@x.com",
        }
        out = AuthService.register_request_by_payload(payload)
        self.assertEqual(out["event_id"], 200)
        mock_create.assert_called_once()

    def test_register_request_validation(self):
        with self.assertRaises(ValueError):
            AuthService.register_request_by_payload({"notice_target": "t", "notice_channel": "email"})
        with self.assertRaises(ValueError):
            AuthService.register_request_by_payload(
                {"username": "a", "password": "p", "notice_channel": "fax", "notice_target": "t"},
            )

    @patch("app_user.services.auth_service.update_event_status")
    @patch("app_user.services.auth_service.create_user")
    @patch("app_user.services.auth_service.verify_payload_code_for_pending_event")
    def test_register_verify_returns_tokens(
        self, mock_v, mock_create, mock_ev,
    ):
        from app_user.enums import EventBizTypeEnum

        ev = SimpleNamespace(id=1)
        mock_v.return_value = (
            ev,
            {
                "username": "nu",
                "password_hash": make_password("pw"),
                "email": "",
                "phone": "",
                "avatar": "",
                "ext": {},
            },
        )
        user = MagicMock()
        user.id = 8
        user.username = "nu"
        user.status = UserStatusEnum.DISABLED.value
        mock_create.return_value = user
        out = AuthService.register_verify_by_payload({"event_id": 1, "code": "ok"})
        self.assertIn("access_token", out)
        self.assertIn("user", out)
        user.save.assert_called_once()
        mock_ev.assert_called_once()


class TestAuthServiceVerifyPasswordResetPayload(SimpleTestCase):
    @patch("app_user.services.auth_service.AuthService._verify_password_reset")
    def test_verify_password_reset_by_payload_parses_int_event_id(self, mock_v):
        mock_v.return_value = True
        out = AuthService.verify_password_reset_by_payload(
            {"event_id": "12", "code": " c ", "new_password": "x"},
        )
        self.assertTrue(out["reset"])
        mock_v.assert_called_once_with(event_id=12, code="c", new_password="x")
