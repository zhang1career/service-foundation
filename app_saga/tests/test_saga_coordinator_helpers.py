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
        inst.step_payloads = "{}"
        inst.start_body = (
            '{"access_key":"k","flow_id":1,"context":{},"step_payloads":{},"idem_key":1}'
        )
        inst.need_confirm = None
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
        self.assertIsNone(out["need_confirm"])
        self.assertEqual(out["saga_shared"]["step_payloads"], {})
        self.assertEqual(len(out["step_runs"]), 1)
        self.assertEqual(out["step_runs"][0]["step_index"], 0)

    def test_load_start_request_empty(self):
        inst = MagicMock()
        inst.start_body = ""
        self.assertEqual(saga_coordinator._load_start_request(inst), {})

    def test_load_start_request_parses(self):
        inst = MagicMock()
        inst.start_body = (
            '{"access_key":"k","flow_id":1,"context":{"a":1},'
            '"step_payloads":{"0":{}},"idem_key":9}'
        )
        out = saga_coordinator._load_start_request(inst)
        self.assertEqual(out["access_key"], "k")
        self.assertEqual(out["flow_id"], 1)
        self.assertEqual(out["context"], {"a": 1})
        self.assertEqual(out["idem_key"], 9)

    def test_load_start_request_invalid_returns_empty(self):
        inst = MagicMock()
        inst.start_body = "not-json"
        self.assertEqual(saga_coordinator._load_start_request(inst), {})

    def test_payload_for_step_prefers_step_code(self):
        st = MagicMock()
        st.step_index = 0
        st.step_code = "pay"
        st.name = "ignored"
        p = {
            "pay": {"k": 1},
            "0": {"i": 2},
        }
        out = saga_coordinator._payload_for_step(st, p)
        self.assertEqual(out, {"k": 1})
