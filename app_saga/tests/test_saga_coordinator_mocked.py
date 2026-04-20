"""saga_coordinator — mocks only, no ``saga_rw`` (aligned with ``app_tcc`` lifecycle tests)."""

from contextlib import nullcontext
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from app_saga.enums import SagaInstanceStatus
from app_saga.services import saga_coordinator
from common.enums.service_reg_status_enum import ServiceRegStatus


class SagaCoordinatorLookupMockedTests(SimpleTestCase):
    @patch("app_saga.services.saga_coordinator.SagaInstance.objects")
    def test_get_instance_by_id(self, mock_objects):
        inst = MagicMock()
        mock_objects.using.return_value.select_related.return_value.filter.return_value.first.return_value = inst
        self.assertIs(saga_coordinator.get_instance_by_id(3), inst)

    @patch("app_saga.services.saga_coordinator.SagaInstance.objects")
    def test_get_instance_by_idem(self, mock_objects):
        inst = MagicMock()
        mock_objects.using.return_value.select_related.return_value.filter.return_value.first.return_value = inst
        self.assertIs(saga_coordinator.get_instance_by_idem(99), inst)


class SagaCoordinatorStartMockedTests(SimpleTestCase):
    @patch("app_saga.services.saga_coordinator.serialize_instance", return_value={"cached": True})
    @patch("app_saga.services.saga_coordinator.get_instance_by_idem")
    @patch(
        "app_saga.services.saga_coordinator._ordered_steps",
        return_value=[MagicMock(pk=1, step_index=0)],
    )
    @patch("app_saga.services.saga_coordinator.SagaFlow.objects.using")
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_start_instance_idempotent_returns_existing(
        self,
        mock_gp,
        mock_flow_using,
        _mock_ordered,
        mock_by_idem,
        mock_serialize,
    ):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.ENABLED.value)
        chain = MagicMock()
        mock_flow_using.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = MagicMock(pk=5, status=ServiceRegStatus.ENABLED.value)
        existing = MagicMock()
        mock_by_idem.return_value = existing
        out = saga_coordinator.start_instance(
            access_key="k",
            flow_id=5,
            context=None,
            idem_key=42,
            step_payloads=None,
        )
        self.assertEqual(out, {"cached": True})
        mock_serialize.assert_called_once_with(existing)

    @patch("app_saga.services.saga_coordinator._ordered_steps", return_value=[])
    @patch("app_saga.services.saga_coordinator.SagaFlow.objects.using")
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_start_instance_rejects_flow_without_steps(
        self,
        mock_gp,
        mock_flow_using,
        _mock_steps,
    ):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.ENABLED.value)
        chain = MagicMock()
        mock_flow_using.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = MagicMock(pk=9, status=ServiceRegStatus.ENABLED.value)
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=9,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("no steps", str(ctx.exception).lower())

    @override_settings(SAGA_START_SYNC_STEP_BUDGET=0)
    @patch("app_saga.services.saga_coordinator.serialize_instance", return_value={"ok": True})
    @patch("app_saga.services.saga_coordinator.get_instance_by_id")
    @patch(
        "app_saga.services.saga_coordinator.get_instance_by_idem",
        return_value=None,
    )
    @patch("app_saga.services.saga_coordinator.process_instance")
    @patch("app_saga.services.saga_coordinator.SagaStepRun")
    @patch("app_saga.services.saga_coordinator.SagaInstance")
    @patch("app_saga.services.saga_coordinator._ordered_steps")
    @patch("django.db.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.saga_coordinator.SagaFlow.objects.using")
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_start_instance_respects_sync_step_budget_zero(
        self,
        mock_gp,
        mock_flow_using,
        mock_ordered,
        mock_si_cls,
        mock_sr_cls,
        mock_process,
        _mock_by_idem,
        mock_get_by_id,
        mock_serialize,
    ):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.ENABLED.value)
        chain = MagicMock()
        mock_flow_using.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = MagicMock(pk=9, status=ServiceRegStatus.ENABLED.value)
        mock_ordered.return_value = [MagicMock(pk=100, step_index=0)]
        inst = MagicMock(pk=555)
        mock_si_cls.return_value = inst
        mock_get_by_id.return_value = inst

        out = saga_coordinator.start_instance(
            access_key="k",
            flow_id=9,
            context={},
            idem_key=8001,
            step_payloads=None,
        )

        mock_process.assert_not_called()
        mock_get_by_id.assert_called()
        mock_serialize.assert_called_once()
        called_with = mock_serialize.call_args[0][0]
        self.assertIs(called_with, mock_get_by_id.return_value)
        self.assertEqual(out, {"ok": True})


class SagaCoordinatorProcessInstanceMockedTests(SimpleTestCase):
    @patch("app_saga.services.saga_coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.saga_coordinator.SagaInstance.objects")
    def test_process_instance_missing_row(self, mock_objects):
        qs = (
            mock_objects.using.return_value.select_for_update.return_value.select_related.return_value.filter.return_value
        )
        qs.first.return_value = None
        saga_coordinator.process_instance(999)

    @patch("app_saga.services.saga_coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.saga_coordinator.SagaInstance.objects")
    @patch("app_saga.services.saga_coordinator._now_ms", return_value=1_000)
    def test_process_instance_terminal_noop(self, _mock_now, mock_objects):
        inst = MagicMock()
        inst.status = SagaInstanceStatus.COMPLETED
        qs = (
            mock_objects.using.return_value.select_for_update.return_value.select_related.return_value.filter.return_value
        )
        qs.first.return_value = inst
        saga_coordinator.process_instance(1)

    @patch("app_saga.services.saga_coordinator.transaction.atomic", lambda *a, **k: nullcontext())
    @patch("app_saga.services.saga_coordinator.SagaInstance.objects")
    @patch("app_saga.services.saga_coordinator._now_ms", return_value=5_000)
    def test_process_instance_skips_when_next_retry_in_future(self, _mock_now, mock_objects):
        inst = MagicMock()
        inst.status = SagaInstanceStatus.RUNNING
        inst.next_retry_at = 9_999_999_999_999
        qs = (
            mock_objects.using.return_value.select_for_update.return_value.select_related.return_value.filter.return_value
        )
        qs.first.return_value = inst
        saga_coordinator.process_instance(1)
