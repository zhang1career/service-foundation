"""Pure helpers on coordinator (no database)."""

from datetime import timedelta

from django.test import SimpleTestCase, override_settings

from app_tcc.services import coordinator


@override_settings(
    TCC_PHASE_CONFIRM_TIMEOUT_SECONDS=10,
    TCC_PHASE_CANCEL_TIMEOUT_SECONDS=7,
)
class CoordinatorTimeoutDeltaTests(SimpleTestCase):
    def test_confirm_phase_scales_by_branch_count(self):
        self.assertEqual(
            coordinator.confirm_phase_timeout_delta(2),
            timedelta(seconds=20),
        )

    def test_confirm_phase_minimum_one_branch_slot(self):
        self.assertEqual(
            coordinator.confirm_phase_timeout_delta(0),
            timedelta(seconds=10),
        )

    def test_cancel_phase_scales(self):
        self.assertEqual(
            coordinator.cancel_phase_timeout_delta(3),
            timedelta(seconds=21),
        )


class CoordinatorLookupTests(SimpleTestCase):
    def test_get_transaction_by_global_id_empty(self):
        self.assertIsNone(coordinator.get_transaction_by_global_id(""))
        self.assertIsNone(coordinator.get_transaction_by_global_id("   "))

    def test_get_transaction_by_global_id_invalid_int(self):
        self.assertIsNone(coordinator.get_transaction_by_global_id("not-a-number"))

    def test_get_transaction_for_query_no_args(self):
        self.assertIsNone(
            coordinator.get_transaction_for_query(global_tx_id=None, idem_key=None),
        )
