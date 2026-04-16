"""Tests for ConfigEntryService (mocked repo + condition validate + on_commit)."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from app_config.enums import ConfigEntryPublic
from app_config.services.config_entry_service import ConfigEntryService


def _immediate_on_commit(callback):
    callback()


def _entry_row(**kwargs):
    defaults = dict(
        id=1,
        rid_id=10,
        config_key="app.x",
        condition="{}",
        public=ConfigEntryPublic.PRIVATE,
        value='{"a":1}',
        ct=100,
        ut=200,
    )
    defaults.update(kwargs)
    row = SimpleNamespace(**defaults)
    row.rid = SimpleNamespace(name="RegTen")
    return row


class TestConfigEntryService(SimpleTestCase):
    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    @patch(
        "app_config.services.config_entry_service.normalize_and_validate_condition",
        return_value="",
    )
    def test_create_private_calls_validate(self, mock_norm, mock_repo, mock_bump, _oc):
        mock_repo.create_entry.return_value = _entry_row(id=3, rid_id=10)
        out = ConfigEntryService.create(
            10, "app.x", "{}", '{"x":1}', ConfigEntryPublic.PRIVATE
        )
        mock_norm.assert_called_once_with(10, "{}")
        mock_repo.create_entry.assert_called_once_with(
            10, "app.x", "", '{"x":1}', ConfigEntryPublic.PRIVATE
        )
        mock_bump.assert_called_once_with(10)
        self.assertEqual(out["id"], 3)
        self.assertEqual(out["reg_name"], "RegTen")

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    @patch("app_config.services.config_entry_service.normalize_and_validate_condition")
    def test_create_public_skips_validate(self, mock_norm, mock_repo, mock_bump, _oc):
        mock_repo.create_entry.return_value = _entry_row(id=4, public=ConfigEntryPublic.PUBLIC)
        ConfigEntryService.create(
            10, "app.x", "{}", '{"x":1}', ConfigEntryPublic.PUBLIC
        )
        mock_norm.assert_not_called()
        mock_repo.create_entry.assert_called_once_with(
            10, "app.x", "", '{"x":1}', ConfigEntryPublic.PUBLIC
        )
        mock_bump.assert_called_once_with(10)

    @patch("app_config.services.config_entry_service.normalize_and_validate_condition")
    def test_create_validation_error_no_repo(self, mock_norm):
        mock_norm.side_effect = ValueError("bad condition")
        with self.assertRaises(ValueError) as ctx:
            ConfigEntryService.create(1, "k", "{}", "v", ConfigEntryPublic.PRIVATE)
        self.assertEqual(str(ctx.exception), "bad condition")

    def test_create_requires_config_key(self):
        with self.assertRaises(ValueError) as ctx:
            ConfigEntryService.create(1, "  ", "{}", "v", ConfigEntryPublic.PRIVATE)
        self.assertEqual(str(ctx.exception), "config_key is required")

    def test_create_requires_value(self):
        with self.assertRaises(ValueError) as ctx:
            ConfigEntryService.create(1, "k", "{}", None, ConfigEntryPublic.PRIVATE)
        self.assertEqual(str(ctx.exception), "value is required")

    def test_create_public_rejects_non_empty_condition(self):
        with self.assertRaises(ValueError) as ctx:
            ConfigEntryService.create(
                1, "k", '{"env":"x"}', '{"a":1}', ConfigEntryPublic.PUBLIC
            )
        self.assertIn("public entry condition", str(ctx.exception))

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    @patch("app_config.services.config_entry_service.normalize_and_validate_condition")
    def test_update_with_condition_calls_validate(
        self, mock_norm, mock_repo, mock_bump, _oc
    ):
        mock_norm.return_value = '{"env":"p"}'
        mock_repo.get_entry_by_id.return_value = _entry_row(id=5, rid_id=12)
        mock_repo.update_entry.return_value = _entry_row(
            id=5, rid_id=12, condition='{"env":"p"}'
        )
        ConfigEntryService.update(5, config_key=None, condition='{"env":"p"}', value=None)
        mock_norm.assert_called_once_with(12, '{"env":"p"}')
        mock_repo.update_entry.assert_called_once_with(
            5, None, '{"env":"p"}', None, None
        )
        mock_bump.assert_called_once_with(12)

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    @patch("app_config.services.config_entry_service.normalize_and_validate_condition")
    def test_update_condition_none_skips_validate(self, mock_norm, mock_repo, mock_bump, _oc):
        mock_repo.get_entry_by_id.return_value = _entry_row()
        mock_repo.update_entry.return_value = _entry_row()
        ConfigEntryService.update(1, config_key="new.key", condition=None, value=None)
        mock_norm.assert_not_called()
        mock_repo.update_entry.assert_called_once_with(
            1, "new.key", None, None, None
        )

    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_update_entry_not_found(self, mock_repo):
        mock_repo.get_entry_by_id.return_value = None
        with self.assertRaises(ValueError):
            ConfigEntryService.update(99, config_key="k")

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_update_repo_returns_none(self, mock_repo, mock_bump, _oc):
        mock_repo.get_entry_by_id.return_value = _entry_row()
        mock_repo.update_entry.return_value = None
        with self.assertRaises(ValueError):
            ConfigEntryService.update(1, config_key="k", condition=None, value=None)
        mock_bump.assert_not_called()

    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_delete_get_not_found(self, mock_repo):
        mock_repo.get_entry_by_id.return_value = None
        with self.assertRaises(ValueError):
            ConfigEntryService.delete(1)

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_delete_delete_false(self, mock_repo, mock_bump, _oc):
        mock_repo.get_entry_by_id.return_value = _entry_row()
        mock_repo.delete_entry.return_value = False
        with self.assertRaises(ValueError):
            ConfigEntryService.delete(1)
        mock_bump.assert_not_called()

    @patch("common.utils.django_util.transaction.on_commit", side_effect=_immediate_on_commit)
    @patch("app_config.services.config_entry_service.bump_config_cache_generation")
    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_delete_success(self, mock_repo, mock_bump, _oc):
        mock_repo.get_entry_by_id.return_value = _entry_row()
        mock_repo.delete_entry.return_value = True
        self.assertTrue(ConfigEntryService.delete(1))
        mock_bump.assert_called_once_with(10)

    @patch("app_config.services.config_entry_service.config_entry_repo")
    def test_list_all_to_dict_without_rid_name_uses_empty(self, mock_repo):
        row = SimpleNamespace(
            id=1,
            rid_id=0,
            config_key="k",
            condition="{}",
            public=ConfigEntryPublic.PRIVATE,
            value="{}",
            ct=1,
            ut=2,
        )
        mock_repo.list_all_entries.return_value = [row]
        out = ConfigEntryService.list_all()
        self.assertEqual(out[0]["reg_name"], "")
        self.assertEqual(out[0]["public"], ConfigEntryPublic.PRIVATE)
