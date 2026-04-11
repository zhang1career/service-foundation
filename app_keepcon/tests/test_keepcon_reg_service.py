"""Tests for KeepconRegService (mocked reg_repo)."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_keepcon.services.reg_service import KeepconRegService


class TestKeepconRegService(SimpleTestCase):
    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_create_by_payload_requires_name(self, mock_repo):
        with self.assertRaises(ValueError) as ctx:
            KeepconRegService.create_by_payload({"name": "  ", "status": 1})
        self.assertEqual(str(ctx.exception), "name is required")
        mock_repo.create_reg.assert_not_called()

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_create_by_payload_success(self, mock_repo):
        mock_repo.create_reg.return_value = SimpleNamespace(
            id=3, name="Acme", access_key="abc", status=1, ct=1, ut=2
        )
        out = KeepconRegService.create_by_payload({"name": " Acme ", "status": 1})
        mock_repo.create_reg.assert_called_once_with(name="Acme", status=1)
        self.assertEqual(out["id"], 3)
        self.assertEqual(out["access_key"], "abc")

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_list_all(self, mock_repo):
        mock_repo.list_regs.return_value = [
            SimpleNamespace(id=1, name="a", access_key="k", status=1, ct=0, ut=0),
        ]
        rows = KeepconRegService.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "a")

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_update_not_found(self, mock_repo):
        mock_repo.update_reg.return_value = None
        with self.assertRaises(ValueError) as ctx:
            KeepconRegService.update_by_payload(9, {"name": "x"})
        self.assertEqual(str(ctx.exception), "reg not found")

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_delete_not_found(self, mock_repo):
        mock_repo.delete_reg.return_value = False
        with self.assertRaises(ValueError):
            KeepconRegService.delete(1)

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_delete_success(self, mock_repo):
        mock_repo.delete_reg.return_value = True
        self.assertTrue(KeepconRegService.delete(2))
        mock_repo.delete_reg.assert_called_once_with(2)

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_update_success(self, mock_repo):
        mock_repo.update_reg.return_value = SimpleNamespace(
            id=10, name="new", access_key="ak", status=0, ct=1, ut=9
        )
        out = KeepconRegService.update_by_payload(10, {"name": "new", "status": 0})
        mock_repo.update_reg.assert_called_once_with(reg_id=10, name="new", status=0)
        self.assertEqual(out["name"], "new")
        self.assertEqual(out["status"], 0)

    @patch("app_keepcon.services.reg_service.reg_repo")
    def test_create_default_status_zero(self, mock_repo):
        mock_repo.create_reg.return_value = SimpleNamespace(
            id=1, name="n", access_key="k", status=0, ct=0, ut=0
        )
        KeepconRegService.create_by_payload({"name": "n"})
        mock_repo.create_reg.assert_called_once_with(name="n", status=0)
