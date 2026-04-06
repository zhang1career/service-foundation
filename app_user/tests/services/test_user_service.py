from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_user.enums import EventBizTypeEnum
from app_user.services.user_service import UserService, AUTH_BIT_VERIFY_CODE
from common.consts.query_const import LIMIT_LIST, LIMIT_PAGE


class TestUserService(SimpleTestCase):
    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.get_user_by_id")
    def test_get_me_returns_none_when_user_missing(self, mock_get, mock_to_dict):
        mock_get.return_value = None
        self.assertIsNone(UserService.get_me(user_id=1))
        mock_to_dict.assert_not_called()

    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.get_user_by_id")
    def test_get_me_returns_public_dict(self, mock_get, mock_to_dict):
        row = MagicMock()
        mock_get.return_value = row
        mock_to_dict.return_value = {"id": 5}
        out = UserService.get_me(user_id=5)
        self.assertEqual(out, {"id": 5})
        mock_to_dict.assert_called_once_with(row)

    @patch("app_user.services.user_service.list_users")
    @patch("app_user.services.user_service.user_to_public_dict", side_effect=lambda u: {"id": u})
    def test_list_users_clamps_limit_to_limit_list(self, mock_ser, mock_list):
        mock_list.return_value = ([1, 2], 2)
        UserService.list_users(offset=0, limit=999_999)
        mock_list.assert_called_once_with(offset=0, limit=LIMIT_LIST)

    @patch("app_user.services.user_service.list_users")
    @patch("app_user.services.user_service.user_to_public_dict", side_effect=lambda u: {"id": u})
    def test_list_users_non_positive_limit_uses_limit_page(self, mock_ser, mock_list):
        mock_list.return_value = ([], 0)
        UserService.list_users(offset=0, limit=0)
        mock_list.assert_called_once_with(offset=0, limit=LIMIT_PAGE)

    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.update_user_status")
    def test_set_status_returns_none_when_update_misses(self, mock_upd, mock_to_dict):
        mock_upd.return_value = None
        self.assertIsNone(UserService.set_status(user_id=9, status=1))
        mock_to_dict.assert_not_called()

    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.update_user_status")
    def test_set_status_success(self, mock_upd, mock_to_dict):
        u = MagicMock()
        mock_upd.return_value = u
        mock_to_dict.return_value = {"id": 1}
        out = UserService.set_status(user_id=1, status=1)
        self.assertEqual(out, {"id": 1})


class TestUserServiceUpdateMe(SimpleTestCase):
    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.update_user_profile")
    def test_update_me_avatar_none_skips_upload(self, mock_prof, mock_pub):
        mock_prof.return_value = MagicMock()
        mock_pub.return_value = {"ok": True}
        UserService.update_me(1, None, None, None, None)
        mock_prof.assert_called_once()
        call_kw = mock_prof.call_args.kwargs
        self.assertIsNone(call_kw.get("avatar"))

    @patch("app_user.services.user_service.upload_avatar")
    @patch("app_user.services.user_service.user_to_public_dict")
    @patch("app_user.services.user_service.update_user_profile")
    def test_update_me_passes_avatar_url(self, mock_prof, mock_pub, mock_up):
        mock_up.return_value = "/api/oss/b/p.png"
        mock_prof.return_value = MagicMock()
        mock_pub.return_value = {}
        UserService.update_me(1, None, None, "data", None)
        mock_up.assert_called_once_with("data")
        self.assertEqual(mock_prof.call_args.kwargs["avatar"], "/api/oss/b/p.png")


class TestUserServiceUpdateMeRequest(SimpleTestCase):
    def test_update_me_request_invalid_channel(self):
        with self.assertRaises(ValueError):
            UserService.update_me_request_by_payload(
                1,
                {"notice_channel": "fax", "notice_target": "t"},
            )

    def test_update_me_request_missing_target(self):
        with self.assertRaises(ValueError):
            UserService.update_me_request_by_payload(
                1,
                {"notice_channel": "email", "notice_target": ""},
            )

    @patch("app_user.services.user_service.create_verify_event_and_send_notice")
    def test_update_me_request_success(self, mock_create):
        mock_create.return_value = SimpleNamespace(id=77)
        out = UserService.update_me_request_by_payload(
            1,
            {"notice_channel": "email", "notice_target": "a@b.c", "email": "new@b.c"},
        )
        self.assertEqual(out["event_id"], 77)
        mock_create.assert_called_once()
        self.assertEqual(
            mock_create.call_args.kwargs["biz_type"],
            EventBizTypeEnum.UPDATE_PROFILE,
        )


class TestUserServiceUpdateMeVerify(SimpleTestCase):
    @patch("app_user.services.user_service.update_event_status")
    @patch("app_user.services.user_service.update_user_profile")
    @patch("app_user.services.user_service.verify_payload_code_for_pending_event")
    @patch("app_user.services.user_service.user_to_public_dict")
    def test_update_me_verify_success(
            self, mock_pub, mock_verify, mock_prof, mock_ev,
    ):
        ev = SimpleNamespace(id=3)
        mock_verify.return_value = (ev, {"email": "e@e.com", "phone": None, "avatar": None, "ext": None})
        u = MagicMock()
        mock_prof.return_value = u
        mock_pub.return_value = {"id": 1, "email": "e@e.com"}
        out = UserService.update_me_verify_by_payload(1, {"event_id": 3, "code": "x"})
        self.assertEqual(out["email"], "e@e.com")
        mock_ev.assert_called_once()


class TestUserServiceConsoleDisposition(SimpleTestCase):
    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.clear_user_disposition")
    def test_console_clear_disposition_returns_public_user(self, mock_clear, mock_pub):
        mock_clear.return_value = MagicMock()
        mock_pub.return_value = {"id": 3, "ctrl_status": 0}
        out = UserService.console_clear_disposition(3)
        self.assertEqual(out["ctrl_status"], 0)
        mock_clear.assert_called_once_with(3)


class TestUserServiceListUsers(SimpleTestCase):
    @patch("app_user.services.user_service.list_users")
    @patch("app_user.services.user_service.user_to_public_dict", side_effect=lambda u: {"id": getattr(u, "id", u)})
    def test_list_users_default_limit(self, mock_ser, mock_list):
        mock_list.return_value = ([MagicMock(id=1)], 1)
        page = UserService.list_users(offset=0, limit=10)
        self.assertEqual(page["total_num"], 1)
        self.assertEqual(len(page["data"]), 1)


class TestUserServiceConsoleVerify(SimpleTestCase):
    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.update_event_status")
    @patch("app_user.services.user_service.update_user_auth_status")
    @patch("app_user.services.user_service.post_verify_check")
    @patch("app_user.services.user_service.load_verify_notice_access_keys")
    @patch("app_user.services.user_service.UserService._find_latest_pending_user_auth_event")
    @patch("app_user.services.user_service.get_user_by_id")
    def test_console_verify_success(
            self, mock_gu, mock_find, mock_keys, mock_post, mock_auth, mock_ev, mock_pub,
    ):
        user = MagicMock()
        user.id = 5
        user.auth_status = 0
        mock_gu.return_value = user
        ev = SimpleNamespace(id=9, verify_code_id=2)
        mock_find.return_value = ev
        mock_keys.return_value = ("v", "n")
        mock_post.return_value = {"errorCode": 0}
        updated = MagicMock()
        mock_auth.return_value = updated
        mock_pub.return_value = {"id": 5}
        out = UserService.console_verify_user_by_code(5, " 123 ")
        self.assertEqual(out["auth_status"], AUTH_BIT_VERIFY_CODE)
        mock_auth.assert_called_once()

    @patch("app_user.services.user_service.get_user_by_id")
    def test_console_verify_no_user(self, mock_gu):
        mock_gu.return_value = None
        with self.assertRaises(ValueError) as ctx:
            UserService.console_verify_user_by_code(1, "c")
        self.assertIn("不存在", str(ctx.exception))

    @patch("app_user.services.user_service.UserService._find_latest_pending_user_auth_event")
    @patch("app_user.services.user_service.get_user_by_id")
    def test_console_verify_no_event(self, mock_gu, mock_find):
        mock_gu.return_value = MagicMock(id=1)
        mock_find.return_value = None
        with self.assertRaises(ValueError) as ctx:
            UserService.console_verify_user_by_code(1, "c")
        self.assertIn("验证码", str(ctx.exception))

    @patch("app_user.services.user_service.update_event_status")
    @patch("app_user.services.user_service.post_verify_check")
    @patch("app_user.services.user_service.load_verify_notice_access_keys")
    @patch("app_user.services.user_service.UserService._find_latest_pending_user_auth_event")
    @patch("app_user.services.user_service.get_user_by_id")
    def test_console_verify_bad_code(
            self, mock_gu, mock_find, mock_keys, mock_post, mock_ev,
    ):
        mock_gu.return_value = MagicMock(id=1, auth_status=0)
        mock_find.return_value = SimpleNamespace(id=2, verify_code_id=1)
        mock_keys.return_value = ("v", "n")
        mock_post.return_value = {"errorCode": 1}
        with self.assertRaises(ValueError):
            UserService.console_verify_user_by_code(1, "wrong")
        mock_ev.assert_called_once()


class TestUserServiceConsoleUpdate(SimpleTestCase):
    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.update_user_profile")
    def test_console_update_profile_only(self, mock_prof, mock_pub):
        u = MagicMock()
        mock_prof.return_value = u
        mock_pub.return_value = {"id": 3}
        out = UserService.console_update_user_by_payload(3, {"email": "a@b.c"})
        self.assertEqual(out["id"], 3)

    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.update_user_status")
    @patch("app_user.services.user_service.update_user_profile")
    def test_console_update_status_branch(self, mock_prof, mock_st, mock_pub):
        mock_prof.return_value = MagicMock()
        mock_st.return_value = MagicMock()
        mock_pub.return_value = {"id": 1, "status": 0}
        UserService.console_update_user_by_payload(1, {"status": 2})
        mock_st.assert_called_once_with(user_id=1, status=2)

    @patch("app_user.services.user_service.upload_avatar")
    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.update_user_profile")
    def test_console_update_avatar_upload(self, mock_prof, mock_pub, mock_up):
        mock_up.return_value = "/p.png"
        mock_prof.return_value = MagicMock()
        mock_pub.return_value = {}
        UserService.console_update_user_by_payload(1, {"avatar": "raw"})
        mock_up.assert_called_once_with("raw")

    @patch("app_user.services.user_service.user_to_console_dict")
    @patch("app_user.services.user_service.update_user_profile")
    def test_console_update_clear_avatar_empty_string(self, mock_prof, mock_pub):
        mock_prof.return_value = MagicMock()
        mock_pub.return_value = {}
        UserService.console_update_user_by_payload(1, {"avatar": "  "})
        self.assertEqual(mock_prof.call_args.kwargs["avatar"], "")
