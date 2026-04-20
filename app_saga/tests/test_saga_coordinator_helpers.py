"""Unit tests for saga_coordinator helpers that need no DB."""

from unittest.mock import MagicMock

from django.test import SimpleTestCase

from app_saga.services import saga_coordinator
from common.consts.response_const import RET_OK


class SagaCoordinatorHelperTests(SimpleTestCase):
    def test_serialize_instance_shape(self):
        inst = MagicMock()
        inst.pk = 100
        inst.idem_key = 200
        inst.flow_id = 3
        inst.status = 20
        inst.current_step_index = 1
        inst.retry_count = 0
        inst.last_error = "x" * 600
        inst.context = '{"k":1}'
        ordered = MagicMock()
        row = {
            "step_index": 0,
            "action_status": 10,
            "compensate_status": 10,
            "last_http_status_action": None,
            "last_http_status_compensate": None,
            "last_error_action": "",
            "last_error_compensate": "",
        }
        ordered.values.return_value = [row]
        inst.step_runs.order_by.return_value = ordered

        out = saga_coordinator.serialize_instance(inst)
        self.assertEqual(out["saga_instance_id"], "100")
        self.assertEqual(out["idem_key"], 200)
        self.assertEqual(out["flow_id"], 3)
        self.assertEqual(len(out["last_error"]), 500)
        self.assertEqual(out["context"], {"k": 1})
        self.assertEqual(len(out["step_runs"]), 1)
        self.assertEqual(out["step_runs"][0]["step_index"], 0)
