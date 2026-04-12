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
    def test_branches_required(self):
        factory = APIRequestFactory()
        request = factory.post("/tcc/begin/", {}, format="json")
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data["errorCode"], 0)

    def test_auto_confirm_must_be_boolean(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/tcc/begin/",
            {"branches": [{"branch_meta_id": 1}], "auto_confirm": "yes"},
            format="json",
        )
        response = TccTransactionBeginView.as_view()(request)
        self.assertNotEqual(response.data["errorCode"], 0)

    @patch("app_tcc.views.transaction_api_view.coordinator.begin_transaction")
    def test_success_delegates_to_coordinator(self, mock_begin):
        mock_begin.return_value = {"global_tx_id": "1"}
        factory = APIRequestFactory()
        request = factory.post(
            "/tcc/begin/",
            {"branches": [{"branch_meta_id": 1, "payload": {}}]},
            format="json",
        )
        response = TccTransactionBeginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["errorCode"], 0)
        self.assertEqual(response.data["data"]["global_tx_id"], "1")


class TccTransactionDetailViewTests(SimpleTestCase):
    def test_both_query_params_rejected(self):
        factory = APIRequestFactory()
        request = factory.get(
            "/tcc/detail/",
            {"idem_key": "1", "global_tx_id": "2"},
        )
        response = TccTransactionDetailView.as_view()(request)
        self.assertNotEqual(response.data["errorCode"], 0)

    def test_neither_query_param_rejected(self):
        factory = APIRequestFactory()
        request = factory.get("/tcc/detail/")
        response = TccTransactionDetailView.as_view()(request)
        self.assertNotEqual(response.data["errorCode"], 0)

    def test_idem_key_must_be_int(self):
        factory = APIRequestFactory()
        request = factory.get("/tcc/detail/", {"idem_key": "abc"})
        response = TccTransactionDetailView.as_view()(request)
        self.assertNotEqual(response.data["errorCode"], 0)
