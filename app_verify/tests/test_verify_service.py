from unittest import TestCase
from unittest.mock import MagicMock, patch

from app_verify.services.verify_service import VerifyService
from common.utils.date_util import get_now_timestamp_ms


class VerifyServiceTest(TestCase):
    def test_code_row_awaits_verification_false_when_row_is_none(self):
        self.assertFalse(VerifyService.code_row_awaits_verification(None))

    def test_code_row_awaits_verification_false_when_code_used(self):
        row = MagicMock(used_at=123, expires_at=get_now_timestamp_ms() + 1000)
        self.assertFalse(VerifyService.code_row_awaits_verification(row))

    def test_code_row_awaits_verification_false_when_expired(self):
        row = MagicMock(used_at=0, expires_at=get_now_timestamp_ms() - 1)
        self.assertFalse(VerifyService.code_row_awaits_verification(row))

    @patch("app_verify.services.verify_service.VerifyService._log_request")
    def test_request_code_invalid_level(self, log_request_mock):
        with self.assertRaises(ValueError):
            VerifyService.request_code(level=99, access_key="ak", ref_id=1)
        log_request_mock.assert_called_once()

    @patch("app_verify.services.verify_service.VerifyService._log_request")
    def test_request_code_missing_access_key(self, log_request_mock):
        with self.assertRaises(ValueError):
            VerifyService.request_code(level=1, access_key=" ", ref_id=2)
        log_request_mock.assert_called_once()

    @patch("app_verify.services.verify_service.VerifyService._create_code_for_reg")
    @patch("app_verify.services.verify_service.get_reg_by_access_key")
    def test_request_code_success(self, get_reg_mock, create_code_mock):
        reg = MagicMock(id=7, status=1)
        get_reg_mock.return_value = reg
        create_code_mock.return_value = {"code_id": 8, "code": "123456"}

        out = VerifyService.request_code(level=1, access_key="ak", ref_id=3)

        self.assertEqual(out["code_id"], 8)
        create_code_mock.assert_called_once_with(reg, 1, 3)

    @patch("app_verify.services.verify_service.VerifyService._log_check")
    @patch("app_verify.services.verify_service.mark_verify_code_used")
    @patch("app_verify.services.verify_service.get_verify_code_by_id")
    @patch("app_verify.services.verify_service.get_reg_by_access_key")
    def test_verify_code_success(self, get_reg_mock, get_code_mock, mark_used_mock, log_check_mock):
        reg = MagicMock(id=10, status=1)
        row = MagicMock(
            id=20,
            reg_id=10,
            ref_id=88,
            level=2,
            used_at=0,
            expires_at=get_now_timestamp_ms() + 1000,
            code="654321",
        )
        get_reg_mock.return_value = reg
        get_code_mock.return_value = row

        out = VerifyService.verify_code(code_id=20, code="654321", access_key="ak")

        self.assertTrue(out["verified"])
        self.assertEqual(out["reg_id"], 10)
        mark_used_mock.assert_called_once_with(20)
        self.assertEqual(log_check_mock.call_count, 1)

    @patch("app_verify.services.verify_service.VerifyService._log_check")
    @patch("app_verify.services.verify_service.mark_verify_code_used")
    @patch("app_verify.services.verify_service.get_verify_code_by_id")
    @patch("app_verify.services.verify_service.get_reg_by_access_key")
    def test_verify_code_wrong_code(self, get_reg_mock, get_code_mock, mark_used_mock, log_check_mock):
        reg = MagicMock(id=10, status=1)
        row = MagicMock(
            id=20,
            reg_id=10,
            ref_id=88,
            level=2,
            used_at=0,
            expires_at=get_now_timestamp_ms() + 1000,
            code="654321",
        )
        get_reg_mock.return_value = reg
        get_code_mock.return_value = row

        with self.assertRaises(ValueError):
            VerifyService.verify_code(code_id=20, code="000000", access_key="ak")

        mark_used_mock.assert_not_called()
        self.assertEqual(log_check_mock.call_count, 1)

    def test_request_code_by_payload_requires_integer_level(self):
        with self.assertRaises(ValueError):
            VerifyService.request_code_by_payload({"level": "low", "access_key": "ak", "ref_id": 1})

