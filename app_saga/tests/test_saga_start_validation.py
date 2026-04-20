"""start_instance input validation (no database)."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_saga.services import saga_coordinator
from common.enums.service_reg_status_enum import ServiceRegStatus


class SagaStartValidationTests(SimpleTestCase):
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_invalid_access_key(self, mock_gp):
        mock_gp.return_value = None
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=1,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("access_key", str(ctx.exception).lower())

    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_non_positive_flow_id(self, mock_gp):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.ENABLED.value)
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=0,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("flow_id", str(ctx.exception).lower())

    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_disabled_participant(self, mock_gp):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.DISABLED.value)
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=1,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("access_key", str(ctx.exception).lower())

    @patch("app_saga.services.saga_coordinator.SagaFlow.objects.using")
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_flow_not_owned_by_participant(self, mock_gp, mock_using):
        mock_gp.return_value = MagicMock(pk=7, status=ServiceRegStatus.ENABLED.value)
        chain = MagicMock()
        mock_using.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=99,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("flow_id", str(ctx.exception).lower())

    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_flow_id_must_be_int(self, mock_gp):
        mock_gp.return_value = MagicMock(pk=1, status=ServiceRegStatus.ENABLED.value)
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id="not-int",
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("flow_id", str(ctx.exception).lower())

    @patch("app_saga.services.saga_coordinator.SagaFlow.objects.using")
    @patch("app_saga.services.participant_reg_service.get_participant_by_access_key")
    def test_disabled_flow(self, mock_gp, mock_using):
        mock_gp.return_value = MagicMock(pk=7, status=ServiceRegStatus.ENABLED.value)
        chain = MagicMock()
        mock_using.return_value = chain
        chain.filter.return_value = chain
        flow = MagicMock()
        flow.status = ServiceRegStatus.DISABLED.value
        chain.first.return_value = flow
        with self.assertRaises(ValueError) as ctx:
            saga_coordinator.start_instance(
                access_key="k",
                flow_id=3,
                context=None,
                idem_key=1,
                step_payloads=None,
            )
        self.assertIn("flow_id", str(ctx.exception).lower())
