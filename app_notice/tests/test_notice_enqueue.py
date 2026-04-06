from unittest.mock import MagicMock, patch

import app_notice.dict_registration  # noqa: F401
from django.test import SimpleTestCase

from app_notice.enums import BrokerEnum, ChannelEnum
from app_notice.services.notice_service import enqueue_notice_by_payload, enqueue_resend_notice_record
from common.dict_catalog import get_dict_by_codes


class TestNoticeBrokerDict(SimpleTestCase):
    def test_notice_broker_registered_for_dict_api(self):
        out = get_dict_by_codes("notice_broker")
        self.assertIn("notice_broker", out)
        self.assertTrue(len(out["notice_broker"]) >= 1)

    def test_notice_status_registered_for_dict_api(self):
        out = get_dict_by_codes("notice_status")
        self.assertIn("notice_status", out)
        self.assertEqual(len(out["notice_status"]), 2)

    def test_to_broker_unknown_raises(self):
        with self.assertRaises(ValueError) as ctx:
            BrokerEnum.to_broker(999)
        self.assertIn("unknown broker", str(ctx.exception))


class TestEnqueueNoticeByPayload(SimpleTestCase):
    def test_channel_missing_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            enqueue_notice_by_payload(
                {
                    "access_key": "x",
                    "content": "c",
                    "event_id": 1,
                }
            )
        self.assertIn("channel", str(ctx.exception))

    def test_im_channel_requires_broker(self):
        with self.assertRaises(ValueError) as ctx:
            enqueue_notice_by_payload(
                {
                    "access_key": "x",
                    "channel": ChannelEnum.WECHAT_SERVICE.value,
                    "content": "c",
                    "event_id": 1,
                }
            )
        self.assertIn("broker is required", str(ctx.exception))

    def test_email_rejects_broker(self):
        with self.assertRaises(ValueError) as ctx:
            enqueue_notice_by_payload(
                {
                    "access_key": "x",
                    "channel": ChannelEnum.EMAIL.value,
                    "broker": BrokerEnum.JIANG.value,
                    "target": "a@b.c",
                    "content": "c",
                    "event_id": 1,
                }
            )
        self.assertIn("broker must not be set", str(ctx.exception))

    @patch("app_notice.services.notice_service.get_thread_pool_executor")
    @patch("app_notice.services.notice_service.create_notice_record")
    @patch("app_notice.services.notice_service.get_reg_by_access_key")
    def test_im_with_broker_queues(self, mock_get_reg, mock_create, mock_get_pool):
        mock_get_reg.return_value = MagicMock(id=1, status=1)
        mock_create.return_value = MagicMock(id=99)
        mock_executor = MagicMock()
        mock_get_pool.return_value = mock_executor
        out = enqueue_notice_by_payload(
            {
                "access_key": "k",
                "channel": ChannelEnum.WECHAT_SERVICE.value,
                "broker": BrokerEnum.JIANG.value,
                "target": "",
                "content": "hi",
                "event_id": 1,
            }
        )
        self.assertEqual(out["notice_id"], 99)
        mock_get_pool.assert_called_once()
        mock_executor.submit.assert_called_once()
        mock_create.assert_called_once()
        self.assertEqual(mock_create.call_args.kwargs.get("broker"), BrokerEnum.JIANG.value)


class TestEnqueueResendNoticeRecord(SimpleTestCase):
    @patch("app_notice.services.notice_service.get_thread_pool_executor")
    @patch("app_notice.services.notice_service.update_notice_record_status")
    @patch("app_notice.services.notice_service.get_notice_record_by_id")
    def test_resend_email_queues(self, mock_get, mock_update, mock_get_pool):
        mock_get.return_value = MagicMock(
            id=7,
            status=0,
            channel=ChannelEnum.EMAIL.value,
            broker=0,
            target="a@b.c",
            subject="sub",
            content="body",
        )
        mock_executor = MagicMock()
        mock_get_pool.return_value = mock_executor
        out = enqueue_resend_notice_record(7)
        self.assertEqual(out["notice_id"], 7)
        mock_update.assert_called_once()
        mock_executor.submit.assert_called_once()

    @patch("app_notice.services.notice_service.get_notice_record_by_id")
    def test_resend_raises_when_success(self, mock_get):
        mock_get.return_value = MagicMock(id=1, status=1)
        with self.assertRaises(ValueError) as ctx:
            enqueue_resend_notice_record(1)
        self.assertIn("未成功", str(ctx.exception))

    @patch("app_notice.services.notice_service.get_notice_record_by_id")
    def test_resend_im_without_broker_raises(self, mock_get):
        mock_get.return_value = MagicMock(
            id=1,
            status=0,
            channel=ChannelEnum.WECHAT_SERVICE.value,
            broker=0,
        )
        with self.assertRaises(ValueError) as ctx:
            enqueue_resend_notice_record(1)
        self.assertIn("broker", str(ctx.exception))
