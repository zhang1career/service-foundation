"""saga_scan management command."""

from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase


class SagaScanCommandTests(SimpleTestCase):
    @patch("app_saga.management.commands.saga_scan.process_one")
    @patch("app_saga.management.commands.saga_scan.claim_batch")
    def test_invokes_claim_and_process(self, mock_claim, mock_process_one):
        inst = MagicMock(pk=9)
        mock_claim.return_value = [inst]
        call_command("saga_scan", limit=7)
        mock_claim.assert_called_once_with(limit=7)
        mock_process_one.assert_called_once_with(inst)
