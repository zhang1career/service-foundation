from unittest.mock import patch, Mock

from django.test import SimpleTestCase, override_settings

from app_notice.services.email_notice_service import EmailNoticeService
from app_notice.services.sms_notice_service import SmsNoticeService


class TestNoticeService(SimpleTestCase):
    @patch("app_notice.services.notice_service.create_notice_record")
    @patch("app_notice.services.email_notice_service.send_mail")
    @override_settings(EMAIL_HOST_USER="noreply@example.com")
    def test_email_notice_send(self, mock_send_mail, mock_create_record):
        mock_send_mail.return_value = 1
        result = EmailNoticeService.send(
            subject="subject",
            body="body",
            recipients=["foo@example.com"],
        )
        self.assertEqual(result, 1)

    @patch("app_notice.services.notice_service.create_notice_record")
    @override_settings(SMS_PROVIDER="mock")
    def test_sms_notice_mock_provider(self, mock_create_record):
        self.assertTrue(SmsNoticeService.send(phone="13912345678", content="code:123456"))

    @patch("app_notice.services.notice_service.create_notice_record")
    @patch("app_notice.services.sms_notice_service.requests.post")
    @override_settings(SMS_PROVIDER="http", SMS_HTTP_ENDPOINT="https://example.com/sms", SMS_HTTP_API_KEY="abc")
    def test_sms_notice_http_provider(self, mock_post, mock_create_record):
        mock_post.return_value = Mock(status_code=200)
        self.assertTrue(SmsNoticeService.send(phone="13912345678", content="code:123456"))

