"""Tests for app_notice.services modules (coverage for helpers and branches)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from app_notice.enums import BrokerEnum, ChannelEnum
from app_notice.enums.broker_jiang_enum import BrokerJiangEnum
from app_notice.services import channel_broker_map as channel_broker_map_module
from app_notice.services.email_notice_service import EmailNoticeService
from app_notice.services.notice_service import _send_record
from app_notice.services.reg_service import RegService
from app_notice.services.sms_notice_service import SmsNoticeService


class TestChannelBrokerMap(SimpleTestCase):
    def tearDown(self):
        channel_broker_map_module._map_cache.clear()

    def test_maps_shared_names_and_caches(self):
        from app_notice.services.channel_broker_map import channel_to_broker_channel_ids

        m1 = channel_to_broker_channel_ids(BrokerJiangEnum)
        m2 = channel_to_broker_channel_ids(BrokerJiangEnum)
        self.assertIs(m1, m2)
        self.assertEqual(
            m1[int(ChannelEnum.WECHAT_SERVICE.value)],
            int(BrokerJiangEnum.WECHAT_SERVICE),
        )


class TestRegService(SimpleTestCase):
    @patch("app_notice.services.reg_service.create_reg")
    def test_create_by_payload_ok(self, mock_create):
        reg = MagicMock()
        reg.id = 1
        reg.name = "n"
        reg.access_key = "k"
        reg.status = 1
        reg.ct = 0
        reg.ut = 0
        mock_create.return_value = reg
        out = RegService.create_by_payload({"name": "  hello  ", "status": 1})
        self.assertEqual(out["name"], "n")
        mock_create.assert_called_once()

    def test_create_by_payload_requires_name(self):
        with self.assertRaises(ValueError) as ctx:
            RegService.create_by_payload({"name": "  ", "status": 1})
        self.assertIn("name is required", str(ctx.exception))

    @patch("app_notice.services.reg_service.list_regs")
    def test_list_all(self, mock_list):
        r = MagicMock()
        r.id = 2
        r.name = "x"
        r.access_key = "ak"
        r.status = 1
        r.ct = 1
        r.ut = 2
        mock_list.return_value = [r]
        rows = RegService.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], 2)

    @patch("app_notice.services.reg_service.get_reg_by_id")
    def test_get_one_found_and_not_found(self, mock_get):
        mock_get.return_value = None
        with self.assertRaises(ValueError) as ctx:
            RegService.get_one(99)
        self.assertIn("reg not found", str(ctx.exception))

        reg = MagicMock()
        reg.id = 3
        reg.name = "a"
        reg.access_key = "b"
        reg.status = 1
        reg.ct = 0
        reg.ut = 0
        mock_get.return_value = reg
        self.assertEqual(RegService.get_one(3)["id"], 3)

    @patch("app_notice.services.reg_service.update_reg")
    @patch("app_notice.services.reg_service.get_reg_by_id")
    def test_update_by_payload_not_found(self, mock_get, mock_update):
        mock_update.return_value = None
        with self.assertRaises(ValueError):
            RegService.update_by_payload(1, {"name": "x"})

    @patch("app_notice.services.reg_service.delete_reg")
    def test_delete_not_found(self, mock_delete):
        mock_delete.return_value = False
        with self.assertRaises(ValueError):
            RegService.delete(42)


class TestEmailNoticeServiceValidation(SimpleTestCase):
    @override_settings(EMAIL_HOST_USER="noreply@example.com")
    @patch("app_notice.services.email_notice_service.send_mail")
    def test_send_requires_recipients(self, _mock_mail):
        with self.assertRaises(ValueError) as ctx:
            EmailNoticeService.send(subject="s", body="b", recipients=[])
        self.assertIn("recipients", str(ctx.exception))

    @override_settings(EMAIL_HOST_USER="noreply@example.com")
    @patch("app_notice.services.email_notice_service.send_mail")
    def test_send_requires_subject(self, _mock_mail):
        with self.assertRaises(ValueError) as ctx:
            EmailNoticeService.send(subject="", body="b", recipients=["a@b.c"])
        self.assertIn("subject", str(ctx.exception))

    @override_settings(EMAIL_HOST_USER="noreply@example.com")
    @patch("app_notice.services.email_notice_service.send_mail")
    def test_send_requires_body(self, _mock_mail):
        with self.assertRaises(ValueError) as ctx:
            EmailNoticeService.send(subject="s", body=None, recipients=["a@b.c"])
        self.assertIn("body", str(ctx.exception))


class TestSmsNoticeServiceBranches(SimpleTestCase):
    def test_requires_phone_and_content(self):
        with self.assertRaises(ValueError):
            SmsNoticeService.send(phone="", content="x")
        with self.assertRaises(ValueError):
            SmsNoticeService.send(phone="1", content="")

    @override_settings(SMS_PROVIDER="")
    def test_requires_provider_config(self):
        with self.assertRaises(ValueError) as ctx:
            SmsNoticeService.send(phone="13900000000", content="hi")
        self.assertIn("SMS_PROVIDER", str(ctx.exception))

    @override_settings(SMS_PROVIDER="http", SMS_HTTP_ENDPOINT="")
    def test_http_requires_endpoint(self):
        with self.assertRaises(ValueError) as ctx:
            SmsNoticeService.send(phone="13900000000", content="hi")
        self.assertIn("SMS_HTTP_ENDPOINT", str(ctx.exception))

    @override_settings(SMS_PROVIDER="unknown_provider_xyz")
    def test_unsupported_provider(self):
        with self.assertRaises(ValueError) as ctx:
            SmsNoticeService.send(phone="13900000000", content="hi")
        self.assertIn("Unsupported SMS provider", str(ctx.exception))

    @override_settings(
        SMS_PROVIDER="http",
        SMS_HTTP_ENDPOINT="https://example.com/sms",
        SMS_HTTP_API_KEY="",
    )
    @patch("app_notice.services.sms_notice_service.request_sync")
    def test_http_non_200_returns_false(self, mock_req):
        mock_req.return_value = MagicMock(status_code=500)
        self.assertFalse(SmsNoticeService.send(phone="13900000000", content="hi"))

    @override_settings(
        SMS_PROVIDER="http",
        SMS_HTTP_ENDPOINT="https://example.com/sms",
        SMS_HTTP_API_KEY="k",
    )
    @patch("app_notice.services.sms_notice_service.request_sync")
    def test_http_call_error_returns_false(self, mock_req):
        from common.services.http import HttpCallError

        mock_req.side_effect = HttpCallError("down")
        self.assertFalse(SmsNoticeService.send(phone="13900000000", content="hi"))


class TestSendRecord(SimpleTestCase):
    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.EmailNoticeService.send")
    def test_email_path_success(self, mock_send, mock_update):
        mock_send.return_value = 1
        _send_record(1, ChannelEnum.EMAIL.value, "a@b.c", "sub", "body", 0)
        mock_send.assert_called_once()
        mock_update.assert_called_once()
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 1)
        self.assertEqual(kw["provider"], "django_email")

    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.SmsNoticeService.send")
    def test_sms_path_failure_message(self, mock_sms, mock_update):
        mock_sms.return_value = False
        _send_record(2, ChannelEnum.SMS.value, "13900000000", "", "c", 0)
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 0)
        self.assertEqual(kw["message"], "sms send failed")

    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.BrokerJiangEnum.send_message")
    def test_broker_jiang_success(self, mock_jiang, mock_update):
        mock_jiang.return_value = (True, "ok")
        ch = int(ChannelEnum.WECHAT_SERVICE.value)
        _send_record(3, ch, "", "t", "d", BrokerEnum.JIANG.value)
        mock_jiang.assert_called_once()
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 1)

    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.BrokerJiangEnum.send_message")
    def test_broker_channel_not_in_mapping(self, mock_jiang, mock_update):
        mock_jiang.return_value = (True, "ok")
        # IM-like channel id not present in Channel↔Jiang name map (avoid EMAIL/SMS branches).
        _send_record(4, 999_998, "", "", "d", BrokerEnum.JIANG.value)
        mock_jiang.assert_not_called()
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 0)
        self.assertIn("not supported", kw["message"])

    @patch("app_notice.services.notice_service.update_notice_record_status")
    def test_broker_zero_for_im_channel(self, mock_update):
        _send_record(5, ChannelEnum.WECHAT_SERVICE.value, "", "", "d", 0)
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 0)
        self.assertIn("broker is required", kw["message"])

    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.EmailNoticeService.send")
    def test_exception_becomes_failed_status(self, mock_send, mock_update):
        mock_send.side_effect = RuntimeError("smtp down")
        _send_record(6, ChannelEnum.EMAIL.value, "a@b.c", "s", "b", 0)
        kw = mock_update.call_args.kwargs
        self.assertEqual(kw["status"], 0)
        self.assertIn("smtp down", kw["message"])
