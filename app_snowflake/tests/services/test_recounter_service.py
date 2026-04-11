"""recounter_service tests (repos mocked; no database)."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_snowflake.tests.conftest import neuter_snowflake_recounter_transaction_for_tests

neuter_snowflake_recounter_transaction_for_tests()

from app_snowflake.services.recounter_service import create_or_update_recount, get_recounter


class TestRecounterService(SimpleTestCase):
    @patch("app_snowflake.repos.recounter_repo.get_recounter")
    def test_get_recounter_returns_rc_when_present(self, mock_repo_get):
        row = MagicMock()
        row.rc = 7
        mock_repo_get.return_value = row
        self.assertEqual(get_recounter(1, 2), 7)
        mock_repo_get.assert_called_once_with(1, 2)

    @patch("app_snowflake.repos.recounter_repo.get_recounter", return_value=None)
    def test_get_recounter_returns_none_when_missing(self, mock_repo_get):
        self.assertIsNone(get_recounter(9, 9))
        mock_repo_get.assert_called_once_with(9, 9)

    @patch("app_snowflake.repos.recounter_repo.update_recounter")
    @patch("app_snowflake.repos.recounter_repo.get_recounter")
    def test_create_or_update_creates_when_missing(self, mock_get, mock_update):
        created = MagicMock()
        created.rc = 0
        mock_get.return_value = None
        with patch("app_snowflake.repos.recounter_repo.create_recounter", return_value=created) as mock_create:
            self.assertEqual(create_or_update_recount(1, 2), 0)
        mock_get.assert_called_once_with(1, 2)
        mock_create.assert_called_once_with(datacenter_id=1, machine_id=2)
        mock_update.assert_not_called()

    @patch("app_snowflake.repos.recounter_repo.update_recounter")
    @patch("app_snowflake.repos.recounter_repo.get_recounter")
    def test_create_or_update_increments_existing(self, mock_get, mock_update):
        row = MagicMock()
        row.rc = 0
        row.id = 10
        row.dcid = 1
        row.mid = 2
        row.ct = 100
        mock_get.return_value = row
        self.assertEqual(create_or_update_recount(1, 2), 1)
        mock_update.assert_called_once_with(
            origin=row,
            data_dict={"recount": 1},
        )

    @patch("app_snowflake.repos.recounter_repo.update_recounter")
    @patch("app_snowflake.repos.recounter_repo.get_recounter")
    def test_create_or_update_wraps_rc_with_mask(self, mock_get, mock_update):
        row = MagicMock()
        row.rc = 3
        row.id = 1
        row.dcid = 1
        row.mid = 2
        row.ct = 100
        mock_get.return_value = row
        self.assertEqual(create_or_update_recount(1, 2), 0)
        mock_update.assert_called_once_with(
            origin=row,
            data_dict={"recount": 0},
        )

    @patch("app_snowflake.repos.recounter_repo.get_recounter", return_value=None)
    def test_create_or_update_raises_when_create_fails(self, _mock_get):
        with patch("app_snowflake.repos.recounter_repo.create_recounter", return_value=None):
            with self.assertRaises(Exception) as ctx:
                create_or_update_recount(1, 2)
        self.assertIn("failed to create recounter", str(ctx.exception))

    @patch("app_snowflake.repos.recounter_repo.update_recounter", side_effect=RuntimeError("db error"))
    @patch("app_snowflake.repos.recounter_repo.get_recounter")
    def test_create_or_update_propagates_update_failure(self, mock_get, _mock_update):
        row = MagicMock()
        row.rc = 1
        row.id = 1
        row.dcid = 1
        row.mid = 2
        row.ct = 100
        mock_get.return_value = row
        with self.assertRaises(RuntimeError):
            create_or_update_recount(1, 2)
