from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch

from app_verify.services.reg_service import RegService


class RegServiceTest(TestCase):
    @patch("app_verify.services.reg_service.create_reg")
    def test_create_by_payload_success(self, create_reg_mock):
        reg = SimpleNamespace(id=1, name="n1", access_key="k1", status=1, ct=11, ut=22)
        create_reg_mock.return_value = reg

        out = RegService.create_by_payload({"name": "n1", "status": 1})

        self.assertEqual(out["id"], 1)
        self.assertEqual(out["name"], "n1")
        create_reg_mock.assert_called_once_with(name="n1", status=1)

    def test_create_by_payload_requires_name(self):
        with self.assertRaises(ValueError):
            RegService.create_by_payload({"name": " ", "status": 1})

    @patch("app_verify.services.reg_service.list_regs")
    def test_list_all_success(self, list_regs_mock):
        list_regs_mock.return_value = [
            SimpleNamespace(id=1, name="n1", access_key="k1", status=1, ct=11, ut=22),
            SimpleNamespace(id=2, name="n2", access_key="k2", status=0, ct=33, ut=44),
        ]

        out = RegService.list_all()

        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["name"], "n1")
        self.assertEqual(out[1]["status"], 0)

    @patch("app_verify.services.reg_service.update_reg")
    def test_update_by_payload_not_found(self, update_reg_mock):
        update_reg_mock.return_value = None
        with self.assertRaises(ValueError):
            RegService.update_by_payload(99, {"name": "x"})

    @patch("app_verify.services.reg_service.delete_reg")
    def test_delete_not_found(self, delete_reg_mock):
        delete_reg_mock.return_value = False
        with self.assertRaises(ValueError):
            RegService.delete(99)

