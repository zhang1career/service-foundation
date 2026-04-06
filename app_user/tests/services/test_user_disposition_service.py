from types import SimpleNamespace

from django.test import SimpleTestCase

from app_user.enums import UserDispositionEnum
from app_user.services.user_disposition_service import (
    LOGIN_FORBIDDEN_PUBLIC_MESSAGE,
    error_for_user_disposition,
)
from common.consts.response_const import RET_ACCOUNT_RESTRICTED


class TestUserDispositionService(SimpleTestCase):
    def test_none_returns_no_error(self):
        u = SimpleNamespace(
            ctrl_status=UserDispositionEnum.NONE.value,
            ctrl_reason="",
        )
        self.assertIsNone(error_for_user_disposition(u))

    def test_login_forbidden_returns_public_message_only(self):
        u = SimpleNamespace(
            ctrl_status=UserDispositionEnum.LOGIN_FORBIDDEN.value,
            ctrl_reason="900秒内同一账号失败22次（阈值5）",
        )
        code, msg = error_for_user_disposition(u)
        self.assertEqual(code, RET_ACCOUNT_RESTRICTED)
        self.assertEqual(msg, LOGIN_FORBIDDEN_PUBLIC_MESSAGE)
        self.assertNotIn("900", msg)
        self.assertNotIn("阈值", msg)

    def test_unknown_status_raises(self):
        u = SimpleNamespace(ctrl_status=99, ctrl_reason="x")
        with self.assertRaises(ValueError) as ctx:
            error_for_user_disposition(u)
        self.assertIn("unknown ctrl_status", str(ctx.exception))
