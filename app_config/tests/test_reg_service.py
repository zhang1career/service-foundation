"""Tests for ConfigRegService (mocked reg_repo, immediate on_commit)."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_config.services.reg_service import ConfigRegService


def _immediate_on_commit(callback):
    callback()


class TestConfigRegService(SimpleTestCase):
    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_create_by_payload_requires_name(self, mock_repo, mock_bump, _oc):
        with self.assertRaises(ValueError) as ctx:
            ConfigRegService.create_by_payload({"name": "  ", "status": 1})
        self.assertEqual(str(ctx.exception), "name is required")
        mock_repo.create_reg.assert_not_called()
        mock_bump.assert_not_called()

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_create_by_payload_success(self, mock_repo, mock_bump, _oc):
        mock_repo.create_reg.return_value = SimpleNamespace(
            id=7, name="Acme", access_key="abc123", status=1, ct=10, ut=20
        )
        out = ConfigRegService.create_by_payload({"name": " Acme ", "status": 1})
        mock_repo.create_reg.assert_called_once_with(name="Acme", status=1)
        mock_bump.assert_called_once_with(7)
        self.assertEqual(
            out,
            {
                "id": 7,
                "name": "Acme",
                "access_key": "abc123",
                "status": 1,
                "ct": 10,
                "ut": 20,
            },
        )

    @patch("app_config.services.reg_service.reg_repo")
    def test_list_all_maps_to_dict(self, mock_repo):
        mock_repo.list_regs.return_value = [
            SimpleNamespace(id=1, name="a", access_key="k1", status=1, ct=1, ut=2),
        ]
        rows = ConfigRegService.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], 1)
        self.assertEqual(rows[0]["access_key"], "k1")

    @patch("app_config.services.reg_service.reg_repo")
    def test_get_one_not_found(self, mock_repo):
        mock_repo.get_reg_by_id.return_value = None
        with self.assertRaises(ValueError) as ctx:
            ConfigRegService.get_one(99)
        self.assertEqual(str(ctx.exception), "reg not found")

    @patch("app_config.services.reg_service.reg_repo")
    def test_get_one_found(self, mock_repo):
        mock_repo.get_reg_by_id.return_value = SimpleNamespace(
            id=2, name="b", access_key="k2", status=0, ct=3, ut=4
        )
        d = ConfigRegService.get_one(2)
        self.assertEqual(d["name"], "b")

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_update_by_payload_not_found(self, mock_repo, mock_bump, _oc):
        mock_repo.update_reg.return_value = None
        with self.assertRaises(ValueError):
            ConfigRegService.update_by_payload(1, {"name": "x"})
        mock_bump.assert_not_called()

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_update_by_payload_success(self, mock_repo, mock_bump, _oc):
        mock_repo.update_reg.return_value = SimpleNamespace(
            id=3, name="new", access_key="k", status=1, ct=1, ut=9
        )
        out = ConfigRegService.update_by_payload(3, {"name": "new", "status": 1})
        mock_repo.update_reg.assert_called_once_with(reg_id=3, name="new", status=1)
        mock_bump.assert_called_once_with(3)
        self.assertEqual(out["name"], "new")

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_update_by_payload_name_only(self, mock_repo, mock_bump, _oc):
        mock_repo.update_reg.return_value = SimpleNamespace(
            id=4, name="only", access_key="k", status=0, ct=0, ut=0
        )
        ConfigRegService.update_by_payload(4, {"name": "only"})
        mock_repo.update_reg.assert_called_once_with(reg_id=4, name="only", status=None)
        mock_bump.assert_called_once_with(4)

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_update_by_payload_status_only(self, mock_repo, mock_bump, _oc):
        mock_repo.update_reg.return_value = SimpleNamespace(
            id=8, name="n", access_key="k", status=0, ct=0, ut=0
        )
        ConfigRegService.update_by_payload(8, {"status": 0})
        mock_repo.update_reg.assert_called_once_with(reg_id=8, name=None, status=0)
        mock_bump.assert_called_once_with(8)

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_create_by_payload_default_status_zero(self, mock_repo, mock_bump, _oc):
        mock_repo.create_reg.return_value = SimpleNamespace(
            id=1, name="n", access_key="k", status=0, ct=0, ut=0
        )
        ConfigRegService.create_by_payload({"name": "n"})
        mock_repo.create_reg.assert_called_once_with(name="n", status=0)
        mock_bump.assert_called_once_with(1)

    @patch("app_config.services.reg_service.reg_repo")
    def test_delete_get_not_found(self, mock_repo):
        mock_repo.get_reg_by_id.return_value = None
        with self.assertRaises(ValueError):
            ConfigRegService.delete(1)
        mock_repo.delete_reg.assert_not_called()

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_delete_delete_reg_false(self, mock_repo, mock_bump, _oc):
        mock_repo.get_reg_by_id.return_value = SimpleNamespace(id=5)
        mock_repo.delete_reg.return_value = False
        with self.assertRaises(ValueError):
            ConfigRegService.delete(5)
        mock_bump.assert_called_once_with(5)

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.reg_service.bump_config_cache_generation")
    @patch("app_config.services.reg_service.reg_repo")
    def test_delete_success(self, mock_repo, mock_bump, _oc):
        mock_repo.get_reg_by_id.return_value = SimpleNamespace(id=6)
        mock_repo.delete_reg.return_value = True
        self.assertTrue(ConfigRegService.delete(6))
        mock_bump.assert_called_once_with(6)
        mock_repo.delete_reg.assert_called_once_with(6)
