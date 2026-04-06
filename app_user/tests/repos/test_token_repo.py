"""token_repo: mocked ORM queries (no DB)."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_user.enums.token_status_enum import TokenStatusEnum
from app_user.repos import token_repo


class TestTokenRepo(SimpleTestCase):
    @patch("app_user.repos.token_repo.Token")
    def test_deprecate_all_tokens_for_user_updates_in_use_rows(self, mock_token):
        qs = MagicMock()
        mock_token.objects.using.return_value.filter.return_value = qs
        qs.update.return_value = 3
        n = token_repo.deprecate_all_tokens_for_user(42)
        self.assertEqual(n, 3)
        mock_token.objects.using.assert_called_once_with("user_rw")
        mock_token.objects.using.return_value.filter.assert_called_once_with(
            user_id=42,
            status=TokenStatusEnum.IN_USE.value,
        )
        qs.update.assert_called_once_with(status=TokenStatusEnum.DEPRECATED.value)

    @patch("app_user.repos.token_repo.Token")
    def test_access_token_in_use_exists(self, mock_token):
        mock_token.objects.using.return_value.filter.return_value.exists.return_value = True
        self.assertTrue(
            token_repo.access_token_in_use(user_id=1, access_token="abc"),
        )

    @patch("app_user.repos.token_repo.Token")
    def test_refresh_token_in_use_exists(self, mock_token):
        mock_token.objects.using.return_value.filter.return_value.exists.return_value = True
        self.assertTrue(
            token_repo.refresh_token_in_use(user_id=2, refresh_token="rt"),
        )
