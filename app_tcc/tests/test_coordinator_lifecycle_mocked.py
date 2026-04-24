"""confirm_transaction / cancel_transaction / lookups — mocks only."""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from app_tcc.enums import BranchStatus, CancelReason, GlobalTxStatus
from app_tcc.services import coordinator


@override_settings(
    TCC_PHASE_CONFIRM_TIMEOUT_SECONDS=120,
    TCC_PHASE_CANCEL_TIMEOUT_SECONDS=120,
)
class CoordinatorLifecycleMockedTests(SimpleTestCase):
    @patch("app_tcc.services.coordinator.get_transaction_for_query", return_value=None)
    def test_confirm_transaction_not_found(self, _mock_get):
        with self.assertRaises(ValueError) as ctx:
            coordinator.confirm_transaction(999999999)
        self.assertIn("not found", str(ctx.exception).lower())

    @patch("app_tcc.services.coordinator.get_transaction_for_query")
    def test_confirm_transaction_wrong_state(self, mock_get):
        g = MagicMock()
        g.status = GlobalTxStatus.COMMITTED
        g.pk = 1
        mock_get.return_value = g
        with self.assertRaises(ValueError) as ctx:
            coordinator.confirm_transaction(1)
        self.assertIn("await", str(ctx.exception).lower())

    @patch("app_tcc.services.coordinator.get_transaction_for_query", return_value=None)
    def test_cancel_transaction_not_found(self, _mock_get):
        with self.assertRaises(ValueError) as ctx:
            coordinator.cancel_transaction(999999999, CancelReason.UNPAID)
        self.assertIn("not found", str(ctx.exception).lower())

    @patch("app_tcc.services.coordinator.get_transaction_for_query")
    def test_cancel_transaction_already_terminal(self, mock_get):
        g = MagicMock()
        g.status = GlobalTxStatus.COMMITTED
        g.pk = 1
        mock_get.return_value = g
        with self.assertRaises(ValueError) as ctx:
            coordinator.cancel_transaction(1, CancelReason.UNPAID)
        self.assertIn("terminal", str(ctx.exception).lower())

    @patch("app_tcc.services.coordinator.serialize_transaction", return_value={"ok": True})
    @patch("app_tcc.services.coordinator.execute_cancel_reverse")
    @patch("app_tcc.services.coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_tcc.services.coordinator.get_transaction_for_query")
    def test_cancel_transaction_invokes_cancel_reverse(
        self,
        mock_get,
        mock_exec_cancel,
        mock_serialize,
    ):
        g = MagicMock()
        g.status = GlobalTxStatus.AWAIT_CONFIRM
        g.pk = 7
        b1 = MagicMock()
        b1.status = BranchStatus.TRY_SUCCEEDED
        g.branches.select_related.return_value.order_by.return_value = [b1]
        mock_get.return_value = g

        out = coordinator.cancel_transaction(7, CancelReason.ORDER_CLOSED)

        mock_exec_cancel.assert_called_once()
        self.assertEqual(out, {"ok": True})

    @patch("app_tcc.services.coordinator.TccGlobalTransaction.objects")
    def test_get_transaction_for_query_by_idem_key(self, mock_objects):
        g = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = g

        found = coordinator.get_transaction_for_query(idem_key=42)

        self.assertIs(found, g)
        mock_objects.using.assert_called_once_with("tcc_rw")

    def test_cancel_transaction_invalid_cancel_reason(self):
        with self.assertRaises(ValueError) as ctx:
            coordinator.cancel_transaction(1, 99)
        self.assertIn("cancel_reason", str(ctx.exception).lower())
