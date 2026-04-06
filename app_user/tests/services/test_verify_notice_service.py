from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from app_user.enums import EventBizTypeEnum, EventStatusEnum
from app_user.services import verify_notice_service as vni


@override_settings(
    USER_VERIFY_ACCESS_KEY="verify-key",
    USER_NOTICE_ACCESS_KEY="notice-key",
    VERIFY_REQUEST_URL="http://verify.example/request",
    VERIFY_CHECK_URL="http://verify.example/check",
    NOTICE_SERVICE_URL="http://notice.example/send",
)
class TestLoadVerifyNoticeKeys(SimpleTestCase):
    def test_returns_tuple(self):
        a, b = vni.load_verify_notice_access_keys()
        self.assertEqual(a, "verify-key")
        self.assertEqual(b, "notice-key")


class TestLoadVerifyNoticeKeysMissing(SimpleTestCase):
    @override_settings(USER_VERIFY_ACCESS_KEY="", USER_NOTICE_ACCESS_KEY="n")
    def test_missing_verify_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            vni.load_verify_notice_access_keys()
        self.assertIn("USER_VERIFY_ACCESS_KEY", str(ctx.exception))

    @override_settings(USER_VERIFY_ACCESS_KEY="v", USER_NOTICE_ACCESS_KEY="  ")
    def test_missing_notice_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            vni.load_verify_notice_access_keys()
        self.assertIn("USER_NOTICE_ACCESS_KEY", str(ctx.exception))


class TestRequestVerifyCode(SimpleTestCase):
    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_none_response_marks_failed_and_raises(self, mock_post, mock_st):
        mock_post.return_value = None
        with self.assertRaises(ValueError):
            vni.request_verify_code_for_event(
                event_id=10,
                verify_access_key="k",
                level=1,
            )
        mock_st.assert_called_once()

    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_error_response_marks_failed_and_raises(self, mock_post, mock_st):
        mock_post.return_value = {"errorCode": 1}
        with self.assertRaises(ValueError) as ctx:
            vni.request_verify_code_for_event(
                event_id=10,
                verify_access_key="k",
                level=1,
            )
        self.assertIn("request", str(ctx.exception).lower())
        mock_st.assert_called_once()
        self.assertEqual(mock_st.call_args[0][0], 10)

    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_invalid_data_shape_raises(self, mock_post, mock_st):
        mock_post.return_value = {"errorCode": 0, "data": {"code": "", "code_id": 0, "ref_id": 10}}
        with self.assertRaises(ValueError):
            vni.request_verify_code_for_event(
                event_id=10,
                verify_access_key="k",
                level=1,
            )
        self.assertEqual(mock_st.call_count, 1)

    @patch("app_user.services.verify_notice_service.update_event_after_code")
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_success_returns_code(self, mock_post, mock_after):
        mock_post.return_value = {
            "errorCode": 0,
            "data": {"code": "abc", "code_id": 7, "ref_id": 10},
        }
        code = vni.request_verify_code_for_event(
            event_id=10,
            verify_access_key="k",
            level=2,
        )
        self.assertEqual(code, "abc")
        mock_after.assert_called_once_with(10, verify_code_id=7, verify_ref_id=10)


class TestEnqueueNotice(SimpleTestCase):
    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_notice_error_raises(self, mock_post, mock_st):
        mock_post.return_value = None
        with self.assertRaises(ValueError):
            vni.enqueue_notice_for_event(
                event_id=1,
                notice_access_key="k",
                channel=0,
                target="t",
                subject="s",
                content="c",
            )
        mock_st.assert_called_once()


class TestPostVerifyCheck(SimpleTestCase):
    @patch("app_user.services.verify_notice_service.post")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/check",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_forwards_to_post(self, mock_post):
        mock_post.return_value = {"errorCode": 0}
        out = vni.post_verify_check(verify_access_key="ak", code_id=3, code="999")
        self.assertEqual(out["errorCode"], 0)
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.kwargs["url"], "http://x/check")


class TestVerifyPayloadCode(SimpleTestCase):
    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post_verify_check")
    @patch("app_user.services.verify_notice_service.load_verify_notice_access_keys")
    @patch("app_user.services.verify_notice_service.get_event_by_id")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_missing_event_id_raises(
            self, mock_ge, mock_keys, mock_check, mock_st,
    ):
        with self.assertRaises(ValueError):
            vni.verify_payload_code_for_pending_event(
                payload={"event_id": 0, "code": "x"},
                expected_biz_type=EventBizTypeEnum.REGISTER,
            )

    @patch("app_user.services.verify_notice_service.get_event_by_id")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_wrong_biz_type_raises(self, mock_ge):
        mock_ge.return_value = SimpleNamespace(
            biz_type=999,
            status=EventStatusEnum.PENDING_VERIFY.value,
        )
        with self.assertRaises(ValueError) as ctx:
            vni.verify_payload_code_for_pending_event(
                payload={"event_id": 1, "code": "c"},
                expected_biz_type=EventBizTypeEnum.REGISTER,
            )
        self.assertIn("invalid", str(ctx.exception).lower())

    @patch("app_user.services.verify_notice_service.update_event_status")
    @patch("app_user.services.verify_notice_service.post_verify_check")
    @patch("app_user.services.verify_notice_service.load_verify_notice_access_keys")
    @patch("app_user.services.verify_notice_service.get_event_by_id")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_verify_http_failure_updates_event(self, mock_ge, mock_keys, mock_check, mock_st):
        ev = SimpleNamespace(
            id=5,
            biz_type=EventBizTypeEnum.REGISTER,
            status=EventStatusEnum.PENDING_VERIFY.value,
            verify_code_id=1,
            payload_json='{"k":1}',
        )
        mock_ge.return_value = ev
        mock_keys.return_value = ("vk", "nk")
        mock_check.return_value = {"errorCode": 1}
        with self.assertRaises(ValueError):
            vni.verify_payload_code_for_pending_event(
                payload={"event_id": 5, "code": "bad"},
                expected_biz_type=EventBizTypeEnum.REGISTER,
            )
        mock_st.assert_called_once_with(
            5,
            status=EventStatusEnum.PENDING_VERIFY.value,
            message="waiting for verified",
        )

    @patch("app_user.services.verify_notice_service.post_verify_check")
    @patch("app_user.services.verify_notice_service.load_verify_notice_access_keys")
    @patch("app_user.services.verify_notice_service.get_event_by_id")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_success_returns_event_and_data(self, mock_ge, mock_keys, mock_check):
        ev = SimpleNamespace(
            id=5,
            biz_type=EventBizTypeEnum.REGISTER,
            status=EventStatusEnum.PENDING_VERIFY.value,
            verify_code_id=1,
            payload_json='{"user_id":9}',
        )
        mock_ge.return_value = ev
        mock_keys.return_value = ("vk", "nk")
        mock_check.return_value = {"errorCode": 0}
        e2, data = vni.verify_payload_code_for_pending_event(
            payload={"event_id": 5, "code": "ok"},
            expected_biz_type=EventBizTypeEnum.REGISTER,
        )
        self.assertIs(e2, ev)
        self.assertEqual(data.get("user_id"), 9)


class TestCreateVerifyEventAndSendNotice(SimpleTestCase):
    @patch("app_user.services.verify_notice_service.enqueue_notice_for_event")
    @patch("app_user.services.verify_notice_service.request_verify_code_for_event")
    @patch("app_user.services.verify_notice_service.load_verify_notice_access_keys")
    @patch("app_user.services.verify_notice_service.create_event")
    @override_settings(
        USER_VERIFY_ACCESS_KEY="v",
        USER_NOTICE_ACCESS_KEY="n",
        VERIFY_REQUEST_URL="http://x/r",
        VERIFY_CHECK_URL="http://x/c",
        NOTICE_SERVICE_URL="http://x/n",
    )
    def test_flow_calls_notice_with_formatted_content(
            self, mock_create, mock_keys, mock_req_code, mock_enqueue,
    ):
        ev = SimpleNamespace(id=42)
        mock_create.return_value = ev
        mock_keys.return_value = ("vk", "nk")
        mock_req_code.return_value = "CODE99"
        out = vni.create_verify_event_and_send_notice(
            biz_type=1,
            level=2,
            notice_channel=0,
            notice_target="t@t.com",
            payload_json="{}",
            subject="subj",
            content_template="code={code} id={event_id}",
        )
        self.assertIs(out, ev)
        mock_enqueue.assert_called_once()
        self.assertIn("CODE99", mock_enqueue.call_args.kwargs["content"])
        self.assertIn("42", mock_enqueue.call_args.kwargs["content"])
