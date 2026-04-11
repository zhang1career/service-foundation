"""Tests for ConfigConditionFieldService (mocked repo + on_commit)."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_config.services.condition_field_service import ConfigConditionFieldService


def _immediate_on_commit(callback):
    callback()


def _field_row(**kwargs):
    defaults = dict(
        id=1,
        rid_id=20,
        field_key="env",
        description="environment",
        ct=1,
        ut=2,
    )
    defaults.update(kwargs)
    row = SimpleNamespace(**defaults)
    row.rid = SimpleNamespace(name="CallerA")
    return row


class TestConfigConditionFieldService(SimpleTestCase):
    @patch(
        "common.utils.django_util.transaction.on_commit",
        side_effect=_immediate_on_commit,
    )
    @patch("app_config.services.condition_field_service.bump_config_cache_generation")
    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_create_success(self, mock_repo, mock_bump, _oc):
        mock_repo.create_field.return_value = _field_row(id=9, field_key="env")
        out = ConfigConditionFieldService.create(20, " env ", "prod tier")
        mock_repo.create_field.assert_called_once_with(20, "env", "prod tier")
        mock_bump.assert_called_once_with(20)
        self.assertEqual(out["field_key"], "env")
        self.assertEqual(out["reg_name"], "CallerA")

    def test_create_requires_field_key(self):
        with self.assertRaises(ValueError) as ctx:
            ConfigConditionFieldService.create(1, "  ", "")
        self.assertEqual(str(ctx.exception), "field_key is required")

    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_update_get_not_found(self, mock_repo):
        mock_repo.get_field_by_id.return_value = None
        with self.assertRaises(ValueError):
            ConfigConditionFieldService.update(99, field_key="x")

    @patch(
        "common.utils.django_util.transaction.on_commit",
        side_effect=_immediate_on_commit,
    )
    @patch("app_config.services.condition_field_service.bump_config_cache_generation")
    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_update_update_returns_none(self, mock_repo, mock_bump, _oc):
        mock_repo.get_field_by_id.return_value = _field_row()
        mock_repo.update_field.return_value = None
        with self.assertRaises(ValueError):
            ConfigConditionFieldService.update(1, field_key="x")
        mock_bump.assert_not_called()

    @patch(
        "common.utils.django_util.transaction.on_commit",
        side_effect=_immediate_on_commit,
    )
    @patch("app_config.services.condition_field_service.bump_config_cache_generation")
    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_update_success(self, mock_repo, mock_bump, _oc):
        mock_repo.get_field_by_id.return_value = _field_row()
        mock_repo.update_field.return_value = _field_row(field_key="region", description="r")
        out = ConfigConditionFieldService.update(1, field_key="region", description="r")
        mock_repo.update_field.assert_called_once_with(1, "region", "r")
        mock_bump.assert_called_once_with(20)
        self.assertEqual(out["field_key"], "region")

    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_delete_get_not_found(self, mock_repo):
        mock_repo.get_field_by_id.return_value = None
        with self.assertRaises(ValueError):
            ConfigConditionFieldService.delete(1)

    @patch(
        "common.utils.django_util.transaction.on_commit",
        side_effect=_immediate_on_commit,
    )
    @patch("app_config.services.condition_field_service.bump_config_cache_generation")
    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_delete_delete_false(self, mock_repo, mock_bump, _oc):
        mock_repo.get_field_by_id.return_value = _field_row()
        mock_repo.delete_field.return_value = False
        with self.assertRaises(ValueError):
            ConfigConditionFieldService.delete(1)
        mock_bump.assert_not_called()

    @patch(
        "common.utils.django_util.transaction.on_commit",
        side_effect=_immediate_on_commit,
    )
    @patch("app_config.services.condition_field_service.bump_config_cache_generation")
    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_delete_success(self, mock_repo, mock_bump, _oc):
        mock_repo.get_field_by_id.return_value = _field_row()
        mock_repo.delete_field.return_value = True
        self.assertTrue(ConfigConditionFieldService.delete(1))
        mock_bump.assert_called_once_with(20)

    @patch("app_config.services.condition_field_service.condition_field_repo")
    def test_list_all(self, mock_repo):
        mock_repo.list_all_fields.return_value = [_field_row()]
        rows = ConfigConditionFieldService.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], 1)
