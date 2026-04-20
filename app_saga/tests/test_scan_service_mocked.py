"""scan_service — mocks only (aligned with ``app_tcc.tests.test_scan_service_mocked``)."""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_saga.services.scan_service import claim_batch, process_one


class ScanServiceMockedTests(SimpleTestCase):
    @patch("app_saga.services.scan_service.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.scan_service.SagaInstance.objects")
    def test_claim_batch_returns_empty_list(self, mock_objects):
        sliced = MagicMock()
        sliced.__iter__ = lambda self: iter([])
        mock_objects.using.return_value.select_for_update.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = sliced

        rows = claim_batch(limit=10)

        self.assertEqual(rows, [])

    @patch("app_saga.services.scan_service.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.scan_service.SagaInstance.objects")
    def test_claim_batch_returns_locked_rows(self, mock_objects):
        inst = MagicMock(pk=42)
        sliced = MagicMock()
        sliced.__iter__ = lambda self: iter([inst])
        mock_objects.using.return_value.select_for_update.return_value.filter.return_value.order_by.return_value.__getitem__.return_value = sliced

        rows = claim_batch(limit=3)

        self.assertEqual(rows, [inst])

    @patch("app_saga.services.scan_service.process_instance")
    def test_process_one_invokes_coordinator(self, mock_process):
        inst = MagicMock(pk=7)
        process_one(inst)
        mock_process.assert_called_once_with(7)

    @patch("app_saga.services.scan_service.process_instance", side_effect=RuntimeError("boom"))
    def test_process_one_swallows_exception_and_logs(self, _mock):
        inst = MagicMock(pk=123)
        with self.assertLogs("app_saga.services.scan_service", level="ERROR") as cm:
            process_one(inst)
        self.assertTrue(
            any("saga_scan failed instance_id=123" in line for line in cm.output),
            cm.output,
        )
