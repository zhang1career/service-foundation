"""scan_service — mocks only."""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_tcc.enums import GlobalTxStatus
from app_tcc.services.scan_service import claim_batch, process_one


class ScanServiceMockedTests(SimpleTestCase):
    @patch("app_tcc.services.scan_service.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_tcc.services.scan_service.TccGlobalTransaction.objects")
    def test_claim_batch_returns_empty_list(self, mock_objects):
        sliced = MagicMock()
        sliced.__iter__ = lambda self: iter([])
        mock_objects.using.return_value.select_for_update.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = sliced

        rows = claim_batch(limit=10)

        self.assertEqual(rows, [])

    def test_process_one_committed_returns_early(self):
        g = MagicMock()
        g.status = GlobalTxStatus.COMMITTED
        process_one(g)
        g.refresh_from_db.assert_called_once()

    def test_process_one_needs_manual_returns_early(self):
        g = MagicMock()
        g.status = GlobalTxStatus.NEEDS_MANUAL
        process_one(g)
        g.refresh_from_db.assert_called_once()
