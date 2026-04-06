from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from app_notice.enums import ChannelEnum
from app_notice.enums.broker_jiang_enum import BrokerJiangEnum


class TestBrokerJiangEnum(SimpleTestCase):
    @override_settings(NOTICE_BROKER_JIANG_SEND_KEY="SCTsend")
    @patch("app_notice.enums.broker_jiang_enum.request_sync")
    def test_send_success_code_zero(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.content = b'{"code":0,"message":"success"}'
        ok, msg = BrokerJiangEnum.send_message(
            title="t",
            desp="body",
            channel=int(BrokerJiangEnum.WECHAT_SERVICE),
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")
        call = mock_request.call_args.kwargs
        self.assertEqual(call["method"], "POST")
        self.assertIn("SCTsend.send", call["url"])
        self.assertEqual(call["headers"]["Content-Type"], "application/json; charset=utf-8")
        self.assertIn(b'"channel": "9"', call["data"])

    @override_settings(NOTICE_BROKER_JIANG_SEND_KEY="")
    def test_send_fails_when_no_send_key(self):
        ok, msg = BrokerJiangEnum.send_message(
            title="t",
            desp="body",
            channel=9,
        )
        self.assertFalse(ok)
        self.assertIn("NOTICE_BROKER_JIANG_SEND_KEY", msg)

    @override_settings(NOTICE_BROKER_JIANG_SEND_KEY="SCTxxx")
    @patch("app_notice.enums.broker_jiang_enum.request_sync")
    def test_send_failure_nonzero_code(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.content = b'{"code":1,"message":"bad"}'
        ok, msg = BrokerJiangEnum.send_message(title="t", desp="body", channel=9)
        self.assertFalse(ok)
        self.assertEqual(msg, "bad")

    @override_settings(NOTICE_BROKER_JIANG_SEND_KEY="SCTxxx")
    @patch("app_notice.enums.broker_jiang_enum.request_sync")
    def test_send_failure_ignores_msg_field(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.content = b'{"code":1,"msg":"from msg"}'
        ok, msg = BrokerJiangEnum.send_message(title="t", desp="body", channel=9)
        self.assertFalse(ok)
        self.assertEqual(msg, "send failed")

    @override_settings(NOTICE_BROKER_JIANG_SEND_KEY="SCTxxx")
    @patch("app_notice.enums.broker_jiang_enum.request_sync")
    def test_send_failure_default_when_empty_strings(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.content = b'{"code":1,"message":""}'
        ok, msg = BrokerJiangEnum.send_message(title="t", desp="body", channel=9)
        self.assertFalse(ok)
        self.assertEqual(msg, "send failed")


class TestChannelEnumCoversBrokerPaths(SimpleTestCase):
    """Sanity: IM channels used with Jiang mapping exist on ChannelEnum."""

    def test_im_channels_exist(self):
        for name in (
            "WECHAT_SERVICE",
            "WECOM_GROUP",
            "WECOM_APP",
            "DINGDING_GROUP",
            "LARK_GROUP",
        ):
            self.assertIn(name, ChannelEnum.__members__)
