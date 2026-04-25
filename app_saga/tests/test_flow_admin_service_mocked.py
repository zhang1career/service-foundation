"""flow_admin_service — mocks only, no DB.

``@transaction.atomic(using="saga_rw")`` wraps functions with Django's ``Atomic``
at import time; patching ``django.db.transaction.atomic`` later does not remove
that wrapper, and ``Atomic.__enter__`` still opens ``saga_rw`` (forbidden in
``SimpleTestCase``). Call ``func.__wrapped__(...)`` to exercise the undecorated
body (same underlying function object as ``functools.wraps`` exposes).
"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from app_saga.models import SagaFlow, SagaFlowStep
from app_saga.services import flow_admin_service


class FlowAdminServiceMockedTests(SimpleTestCase):
    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_list_all_flows(self, mock_objects):
        mock_objects.using.return_value.select_related.return_value.order_by.return_value = []
        self.assertEqual(flow_admin_service.list_all_flows(), [])

    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_list_flows_for_participant(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.order_by.return_value = []
        self.assertEqual(flow_admin_service.list_flows_for_participant(3), [])

    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_get_flow(self, mock_objects):
        f = MagicMock()
        mock_objects.using.return_value.select_related.return_value.filter.return_value.first.return_value = f
        self.assertIs(flow_admin_service.get_flow(1), f)

    @patch.object(SagaFlow, "save")
    def test_create_flow_strips_name(self, mock_save):
        f = flow_admin_service.create_flow.__wrapped__(
            participant_id=2,
            name="  nm  ",
            status=1,
        )
        self.assertEqual(f.name, "nm")
        self.assertEqual(f.participant_id, 2)
        mock_save.assert_called_once_with(using="saga_rw")

    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_update_flow(self, mock_objects):
        f = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = f
        out = flow_admin_service.update_flow.__wrapped__(9, name="  x  ", status=0)
        self.assertIs(out, f)
        self.assertEqual(f.name, "x")
        self.assertEqual(f.status, 0)
        f.save.assert_called_once_with(using="saga_rw")

    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_update_flow_missing_returns_none(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.first.return_value = None
        self.assertIsNone(flow_admin_service.update_flow.__wrapped__(999, name="a"))

    @patch("app_saga.services.flow_admin_service.SagaFlow.objects")
    def test_delete_flow(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.delete.return_value = (1, {})
        self.assertTrue(flow_admin_service.delete_flow.__wrapped__(1))

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_list_steps_for_flow(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.order_by.return_value = []
        self.assertEqual(flow_admin_service.list_steps_for_flow(1), [])

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_create_rejects_duplicate_step_code(self, mock_objects):
        chain = MagicMock()
        mock_objects.using.return_value = chain
        chain.filter.return_value.exists.return_value = True
        with self.assertRaises(ValueError) as ctx:
            flow_admin_service.create_flow_step.__wrapped__(
                flow_id=1,
                step_code="dup",
                name="n",
                action_url="u",
                compensate_url="v",
            )
        self.assertIn("unique", str(ctx.exception).lower())

    @patch.object(SagaFlowStep, "save")
    @patch(
        "app_saga.services.flow_admin_service.list_steps_for_flow",
        return_value=[],
    )
    def test_create_flow_step_first_index_zero(self, _mock_list, mock_save):
        s = flow_admin_service.create_flow_step.__wrapped__(
            flow_id=1,
            step_code="a",
            name=" a ",
            action_url=" http://a ",
            compensate_url=" http://c ",
        )
        self.assertEqual(s.step_index, 0)
        self.assertEqual(s.name, "a")
        self.assertEqual(s.step_code, "a")
        mock_save.assert_called_once_with(using="saga_rw")

    @patch.object(SagaFlowStep, "save")
    @patch("app_saga.services.flow_admin_service.list_steps_for_flow")
    def test_create_flow_step_increments_index(self, mock_list, mock_save):
        prev = MagicMock()
        prev.step_index = 2
        mock_list.return_value = [prev]
        s = flow_admin_service.create_flow_step.__wrapped__(
            flow_id=1,
            step_code="b",
            name="b",
            action_url="u",
            compensate_url="v",
        )
        self.assertEqual(s.step_index, 3)

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_update_flow_step(self, mock_objects):
        s = MagicMock()
        mock_objects.using.return_value.filter.return_value.first.return_value = s
        out = flow_admin_service.update_flow_step.__wrapped__(1, timeout_sec=99)
        self.assertIs(out, s)
        self.assertEqual(s.timeout_sec, 99)
        s.save.assert_called_once_with(using="saga_rw")

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_delete_flow_step(self, mock_objects):
        mock_objects.using.return_value.filter.return_value.delete.return_value = (1, {})
        self.assertTrue(flow_admin_service.delete_flow_step.__wrapped__(3))

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_reorder_flow_steps(self, mock_objects):
        r0 = MagicMock()
        r0.id = 10
        r0.step_index = 0
        r1 = MagicMock()
        r1.id = 11
        r1.step_index = 1
        mock_objects.using.return_value.filter.return_value.order_by.return_value = [r0, r1]
        flow_admin_service.reorder_flow_steps.__wrapped__(7, [11, 10])
        self.assertEqual(r1.save.call_count, 2)
        self.assertEqual(r0.save.call_count, 2)

    @patch("app_saga.services.flow_admin_service.SagaFlowStep.objects")
    def test_reorder_flow_steps_validation(self, mock_objects):
        r0 = MagicMock()
        r0.id = 10
        r0.step_index = 0
        mock_objects.using.return_value.filter.return_value.order_by.return_value = [r0]
        with self.assertRaises(ValueError) as ctx:
            flow_admin_service.reorder_flow_steps.__wrapped__(1, [])
        self.assertIn("required", str(ctx.exception).lower())
        with self.assertRaises(ValueError) as ctx:
            flow_admin_service.reorder_flow_steps.__wrapped__(1, [10, 10])
        self.assertIn("mismatch", str(ctx.exception).lower())
        with self.assertRaises(ValueError) as ctx:
            flow_admin_service.reorder_flow_steps.__wrapped__(1, [99])
        self.assertIn("mismatch", str(ctx.exception).lower())
