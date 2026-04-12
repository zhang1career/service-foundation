"""tcc_scan management command."""

from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase


class TccScanCommandTests(SimpleTestCase):
    @patch("app_tcc.management.commands.tcc_scan.process_one")
    @patch("app_tcc.management.commands.tcc_scan.claim_batch")
    def test_handle_processes_claimed_rows(self, mock_claim, mock_process):
        g1 = MagicMock()
        g1.pk = 101
        g2 = MagicMock()
        g2.pk = 102
        mock_claim.return_value = [g1, g2]

        call_command("tcc_scan", limit=7)

        mock_claim.assert_called_once_with(limit=7)
        self.assertEqual(mock_process.call_count, 2)
        mock_process.assert_any_call(g1)
        mock_process.assert_any_call(g2)

    @patch("app_tcc.management.commands.tcc_scan.process_one")
    @patch("app_tcc.management.commands.tcc_scan.claim_batch")
    def test_handle_swallows_process_exception(self, mock_claim, mock_process):
        g = MagicMock()
        g.pk = 9
        mock_claim.return_value = [g]
        mock_process.side_effect = RuntimeError("boom")

        call_command("tcc_scan", limit=50)

        mock_process.assert_called_once_with(g)
