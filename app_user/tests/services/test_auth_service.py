from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.hashers import make_password
from django.test import SimpleTestCase, override_settings

from app_user.enums import UserStatusEnum
from app_user.services.auth_service import AuthService
from app_user.utils.jwt_util import create_refresh_token, decode_token
from common.consts.response_const import (
    RET_ACCOUNT_RESTRICTED,
    RET_DUPLICATE_REQUEST,
    RET_RATE_LIMITED,
    RET_TOKEN_REVOKED,
)
from common.exceptions.base_exception import CheckedException


def _login_user_stub(**kwargs):
    base = dict(
        id=1,
        phone="",
        avatar="",
        ext="{}",
        auth_status=0,
        ctrl_status=0,
        ctrl_reason="",
        ct=0,
        ut=0,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class TestAuthService(SimpleTestCase):
    """Login paths call get_user_by_login; mock repo like app_aibroker view tests."""

    @patch("app_user.services.auth_service.clear_on_success")
    @patch("app_user.services.auth_service.replace_session_tokens")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login(self, mock_get, mock_replace, mock_clear):
        mock_get.return_value = _login_user_stub(
            id=1,
            username="user1",
            email="user1@example.com",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("pass1234"),
        )
        logged_in = AuthService.login(
            login_key="user1",
            password="pass1234",
            client_ip="127.0.0.1",
        )
        self.assertIn("access_token", logged_in)
        self.assertEqual(logged_in["user"]["username"], "user1")
        mock_get.assert_called_once_with("user1")
        mock_replace.assert_called_once()
        mock_clear.assert_called_once_with("user1", "127.0.0.1")

    def test_login_empty_credentials_raises(self):
        with self.assertRaises(ValueError) as ctx:
            AuthService.login(login_key="", password="x", client_ip="127.0.0.1")
        self.assertIn("required", str(ctx.exception).lower())

    @patch("app_user.services.auth_service.record_failure")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_wrong_password_raises(self, mock_get, mock_record):
        mock_get.return_value = _login_user_stub(
            id=2,
            username="user2",
            email="user2@example.com",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("secret"),
        )
        mock_record.return_value = (1, 1)
        with self.assertRaises(ValueError) as ctx:
            AuthService.login(login_key="user2", password="wrong", client_ip="127.0.0.1")
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
    """Refresh uses JWT + DB rotation (mocked)."""

    @patch("app_user.services.auth_service.rotate_refresh_row", return_value=True)
    @patch("app_user.services.auth_service.refresh_token_in_use", return_value=True)
    @patch("app_user.services.auth_service.error_for_user_disposition", return_value=None)
    @patch("app_user.services.auth_service.get_user_by_id")
    def test_refresh_returns_access_and_refresh_tokens(self, mock_get_user, *_mocks):
        mock_get_user.return_value = _login_user_stub(
            id=99,
            username="token_user",
            status=UserStatusEnum.ENABLED.value,
        )
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
    @patch("app_user.services.auth_service.transaction.atomic")
    @patch("app_user.services.auth_service.deprecate_all_tokens_for_user")
    @patch("app_user.services.auth_service.update_event_status")
    @patch("app_user.services.auth_service.update_user_password")
    @patch("app_user.services.auth_service.post_verify_check")
    @patch("app_user.services.auth_service.load_verify_notice_access_keys")
    @patch("app_user.services.auth_service.get_user_by_id")
    @patch("app_user.services.auth_service.get_event_by_id")
    def test_verify_success(
            self,
            mock_ge,
            mock_gu,
            mock_keys,
            mock_post,
            mock_upd_pw,
            mock_upd_ev,
            mock_dep,
            mock_atomic,
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
        mock_atomic.side_effect = lambda **kwargs: nullcontext()
        ok = AuthService._verify_password_reset(
            event_id=7,
            code="999",
            new_password="newpass1",
        )
        self.assertTrue(ok)
        mock_upd_pw.assert_called_once()
        mock_upd_ev.assert_called_once()
        mock_dep.assert_called_once_with(3)

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
    @patch("app_user.services.auth_service.latest_incomplete_register_event_by_notice")
    def test_register_request_success(
            self, mock_prior, mock_u, mock_e, mock_p, mock_av, mock_create,
    ):
        mock_prior.return_value = None
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

    @override_settings(VERIFY_CODE_TTL_SECONDS=300)
    @patch("app_user.services.auth_service.create_verify_event_and_send_notice")
    @patch("app_user.services.auth_service.upload_avatar")
    @patch("app_user.services.auth_service.get_user_by_phone")
    @patch("app_user.services.auth_service.get_user_by_email")
    @patch("app_user.services.auth_service.get_user_by_username")
    @patch("app_user.services.auth_service.latest_incomplete_register_event_by_notice")
    @patch("app_user.services.auth_service.get_now_timestamp_ms")
    def test_register_request_rejects_duplicate_within_ttl(
            self, mock_now, mock_prior, mock_u, mock_e, mock_p, mock_av, mock_create,
    ):
        mock_u.return_value = None
        mock_e.return_value = None
        mock_p.return_value = None
        mock_av.return_value = ""
        mock_now.return_value = 1_000_000
        mock_prior.return_value = SimpleNamespace(ct=999_000, id=501)
        payload = {
            "username": "newu",
            "password": "secret12",
            "email": "",
            "phone": "",
            "notice_channel": "email",
            "notice_target": "newu@x.com",
        }
        with self.assertRaises(CheckedException) as ctx:
            AuthService.register_request_by_payload(payload)
        self.assertEqual(ctx.exception.ret_code, RET_DUPLICATE_REQUEST)
        self.assertEqual(ctx.exception.data, {"event_id": 501})
        mock_create.assert_not_called()

    def test_register_request_validation(self):
        with self.assertRaises(ValueError):
            AuthService.register_request_by_payload({"notice_target": "t", "notice_channel": "email"})
        with self.assertRaises(ValueError):
            AuthService.register_request_by_payload(
                {"username": "a", "password": "p", "notice_channel": "fax", "notice_target": "t"},
            )

    @patch("app_user.services.auth_service.transaction.atomic")
    @patch("app_user.services.auth_service.replace_session_tokens")
    @patch("app_user.services.auth_service.update_event_status")
    @patch("app_user.services.auth_service.create_user")
    @patch("app_user.services.auth_service.verify_payload_code_for_pending_event")
    def test_register_verify_returns_tokens(
            self, mock_v, mock_create, mock_ev, mock_replace, mock_atomic,
    ):
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
        mock_atomic.side_effect = lambda **kwargs: nullcontext()
        out = AuthService.register_verify_by_payload({"event_id": 1, "code": "ok"})
        self.assertIn("access_token", out)
        self.assertIn("user", out)
        user.save.assert_called_once()
        mock_ev.assert_called_once()
        mock_replace.assert_called_once()


class TestAuthServiceVerifyPasswordResetPayload(SimpleTestCase):
    @patch("app_user.services.auth_service.AuthService._verify_password_reset")
    def test_verify_password_reset_by_payload_parses_int_event_id(self, mock_v):
        mock_v.return_value = True
        out = AuthService.verify_password_reset_by_payload(
            {"event_id": "12", "code": " c ", "new_password": "x"},
        )
        self.assertTrue(out["reset"])
        mock_v.assert_called_once_with(event_id=12, code="c", new_password="x")


class TestAuthServiceLoginSecurity(SimpleTestCase):
    @patch("app_user.services.auth_service.bump_disposition_login_throttle", return_value=1)
    @patch("app_user.services.auth_service.error_for_user_disposition")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_disposition_raises_checked_exception(self, mock_get, mock_disp, _mock_bump):
        mock_get.return_value = _login_user_stub(
            username="blocked",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("p"),
        )
        mock_disp.return_value = (RET_ACCOUNT_RESTRICTED, "账户受限")
        with self.assertRaises(CheckedException) as ctx:
            AuthService.login("blocked", "p", "127.0.0.1")
        self.assertEqual(ctx.exception.ret_code, RET_ACCOUNT_RESTRICTED)
        self.assertEqual(ctx.exception.message, "账户受限")

    @override_settings(USER_DISPOSITION_AUTH_THROTTLE_MAX=10)
    @patch("app_user.services.auth_service.bump_disposition_login_throttle", return_value=10)
    @patch("app_user.services.auth_service.error_for_user_disposition")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_disposition_throttle_returns_rate_limited(
            self, mock_get, mock_disp, _mock_bump,
    ):
        mock_get.return_value = _login_user_stub(
            username="blocked",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("p"),
        )
        mock_disp.return_value = (RET_ACCOUNT_RESTRICTED, "账户受限")
        with self.assertRaises(CheckedException) as ctx:
            AuthService.login("blocked", "p", "127.0.0.1")
        self.assertEqual(ctx.exception.ret_code, RET_RATE_LIMITED)

    @patch("app_user.services.auth_service.AuthService._lock_bruteforce")
    @patch("app_user.services.auth_service.record_failure")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_wrong_password_at_threshold_locks(
            self, mock_get, mock_record, mock_lock,
    ):
        mock_get.return_value = _login_user_stub(
            username="u3",
            status=UserStatusEnum.ENABLED.value,
            password_hash=make_password("secret"),
        )
        mock_record.return_value = (5, 1)
        with self.assertRaises(CheckedException) as ctx:
            AuthService.login("u3", "wrongpass", "127.0.0.1")
        self.assertEqual(ctx.exception.ret_code, RET_ACCOUNT_RESTRICTED)
        mock_lock.assert_called_once_with(mock_get.return_value, lk_count=5)

    @patch("app_user.services.auth_service.record_failure")
    @patch("app_user.services.auth_service.get_user_by_login")
    def test_login_unknown_user_ip_rate_limited(self, mock_get, mock_record):
        mock_get.return_value = None
        mock_record.return_value = (1, 20)
        with self.assertRaises(CheckedException) as ctx:
            AuthService.login("nobody", "pw", "10.0.0.1")
        self.assertEqual(ctx.exception.ret_code, RET_RATE_LIMITED)

    @patch("app_user.services.auth_service.error_for_user_disposition")
    @patch("app_user.services.auth_service.refresh_token_in_use", return_value=True)
    @patch("app_user.services.auth_service.get_user_by_id")
    def test_refresh_disposition_raises_checked_exception(self, mock_get, _mock_in_use, mock_disp):
        mock_get.return_value = _login_user_stub(id=5, username="x")
        mock_disp.return_value = (RET_ACCOUNT_RESTRICTED, "no")
        rt = create_refresh_token(user_id=5, username="x")
        with self.assertRaises(CheckedException) as ctx:
            AuthService.refresh(rt)
        self.assertEqual(ctx.exception.ret_code, RET_ACCOUNT_RESTRICTED)

    @patch("app_user.services.auth_service.refresh_token_in_use", return_value=False)
    @patch("app_user.services.auth_service.error_for_user_disposition", return_value=None)
    @patch("app_user.services.auth_service.get_user_by_id")
    def test_refresh_not_in_database_raises_revoked(self, mock_get, _mock_disp, _mock_ref):
        mock_get.return_value = _login_user_stub(id=7, username="z")
        rt = create_refresh_token(user_id=7, username="z")
        with self.assertRaises(CheckedException) as ctx:
            AuthService.refresh(rt)
        self.assertEqual(ctx.exception.ret_code, RET_TOKEN_REVOKED)
