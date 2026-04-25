"""DRF API views for TCC (no database; coordinator mocked where needed)."""

from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from app_tcc.views.tcc_health_view import TccHealthView
from app_tcc.views.transaction_api_view import (
    TccTransactionBeginView,
    TccTransactionDetailView,
)


class TccHealthViewTests(SimpleTestCase):
    def test_get_returns_ok(self):
        factory = APIRequestFactory()
        request = factory.get("/tcc/health/")
        response = TccHealthView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["errorCode"], 0)
        self.assertEqual(response.data["data"]["service"], "tcc")


class TccTransactionBeginViewTests(SimpleTestCase):
    def test_biz_id_required(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/tcc/tx",
            {"branches": [{"branch_code": "a"}]},
            format="json",
        )
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data["errorCode"], 0)

    def test_branches_required(self):
        factory = APIRequestFactory()
        request = factory.post("/tcc/tx", {"biz_id": 1}, format="json")
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data["errorCode"], 0)

    def test_auto_confirm_must_be_boolean(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/tcc/tx",
            {
                "biz_id": 1,
                "branches": [{"branch_code": "a"}],
                "auto_confirm": "yes",
            },
            format="json",
        )
        response = TccTransactionBeginView.as_view()(request)
        self.assertNotEqual(response.data["errorCode"], 0)

    @patch("app_tcc.views.transaction_api_view.coordinator.begin_transaction")
    def test_success_delegates_to_coordinator(self, mock_begin):
        mock_begin.return_value = {"global_tx_id": "1"}
        factory = APIRequestFactory()
        request = factory.post(
            "/tcc/tx",
            {"biz_id": 1, "branches": [{"branch_code": "a", "payload": {}}]},
            format="json",
        )
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["errorCode"], 0)
        self.assertEqual(response.data["data"]["global_tx_id"], "1")

    @patch("app_tcc.views.transaction_api_view.coordinator.begin_transaction")
    def test_saga_envelope_uses_biz_id_from_payload(self, mock_begin):
        mock_begin.return_value = {"global_tx_id": "9"}
        factory = APIRequestFactory()
        body = {
            "saga_instance_id": "100",
            "flow_id": 5,
            "phase": "action",
            "context": {},
            "saga_shared": {
                "tcc_access_key": "tcc-sec-1",
                "step_payloads": {"0": {}},
            },
            "payload": {
                "biz_id": 1,
                "branches": [
                    {"branch_code": "a", "payload": {}},
                ],
            },
        }
        request = factory.post("/tcc/tx", body, format="json")
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["errorCode"], 0)
        mock_begin.assert_called_once()
        c = mock_begin.call_args
        self.assertEqual(c.kwargs["biz_id"], 1)
        self.assertEqual(len(c.kwargs["branch_items"]), 1)
        self.assertEqual(c.kwargs["branch_items"][0]["branch_code"], "a")

    def test_saga_envelope_requires_payload_biz_id(self):
        factory = APIRequestFactory()
        body = {
            "saga_instance_id": "100",
            "flow_id": 5,
            "phase": "action",
            "context": {},
            "saga_shared": {
                "tcc_access_key": "k",
                "step_payloads": {},
            },
            "payload": {
                "branches": [
                    {"branch_code": "a", "payload": {}},
                ],
            },
        }
        request = factory.post("/tcc/tx", body, format="json")
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertNotEqual(response.data["errorCode"], 0)


class TccTransactionDetailViewTests(SimpleTestCase):
    def test_blank_idem_key_rejected(self):
        factory = APIRequestFactory()
        request = factory.get("/tcc/tx/   ")
        response = TccTransactionDetailView.as_view()(
            request, idem_key="   "
        )
        self.assertNotEqual(response.data["errorCode"], 0)

    @patch("app_tcc.views.transaction_api_view.coordinator.get_transaction_for_query")
    def test_not_found(self, mock_get):
        mock_get.return_value = None
        factory = APIRequestFactory()
        request = factory.get("/tcc/tx/1")
        response = TccTransactionDetailView.as_view()(request, idem_key="1")
        self.assertNotEqual(response.data["errorCode"], 0)

    @patch("app_tcc.views.transaction_api_view.coordinator.serialize_transaction")
    @patch("app_tcc.views.transaction_api_view.coordinator.get_transaction_for_query")
    def test_success(self, mock_get, mock_ser):
        found = object()
        mock_get.return_value = found
        mock_ser.return_value = {"global_tx_id": "1", "branches": []}
        factory = APIRequestFactory()
        request = factory.get("/tcc/tx/1")
        response = TccTransactionDetailView.as_view()(request, idem_key="1")
        self.assertEqual(response.data["errorCode"], 0)
        self.assertEqual(response.data["data"]["global_tx_id"], "1")
        mock_ser.assert_called_once_with(found)
