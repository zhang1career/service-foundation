"""Unit tests for participant HTTP client (no outbound I/O)."""

from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from app_tcc.enums import CancelReason
from app_tcc.services import participant_http
from common.utils.service_url_template import ServiceUrlResolutionError


@override_settings(TCC_OUTBOUND_TIMEOUT_SEC=12.0)
class ParticipantHttpTests(SimpleTestCase):
    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_success_returns_empty_error(
        self, mock_sync, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.text = "ignored"
        mock_sync.return_value = mock_resp

        st, err = participant_http.call_participant(
            url="http://p/x",
            phase=participant_http.PHASE_TRY,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={"a": 1},
        )
        self.assertEqual(st, 204)
        self.assertEqual(err, "")
        mock_sync.assert_called_once()
        call_kw = mock_sync.call_args.kwargs
        self.assertEqual(call_kw["method"], "POST")
        self.assertEqual(call_kw["url"], "http://p/x")
        body = call_kw["json_body"]
        self.assertEqual(body["phase"], participant_http.PHASE_TRY)
        self.assertEqual(body["payload"], {"a": 1})

    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_expands_templated_url(self, mock_sync, mock_expand):
        mock_expand.return_value = "http://h:1/tcc/try"
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.text = ""
        mock_sync.return_value = mock_resp

        participant_http.call_participant(
            url="http://{{pay-svc}}/tcc/try",
            phase=participant_http.PHASE_TRY,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={},
        )
        mock_expand.assert_called_once_with("http://{{pay-svc}}/tcc/try")
        self.assertEqual(mock_sync.call_args.kwargs["url"], "http://h:1/tcc/try")

    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_resolution_error_returns_zero(self, mock_sync, mock_expand):
        mock_expand.side_effect = ServiceUrlResolutionError("no svc")
        st, err = participant_http.call_participant(
            url="http://{{nope}}/a",
            phase=participant_http.PHASE_CANCEL,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={},
        )
        self.assertEqual(st, 0)
        self.assertIn("no svc", err)
        mock_sync.assert_not_called()

    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_failure_returns_snippet(self, mock_sync, mock_expand):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "upstream " + "x" * 600
        mock_sync.return_value = mock_resp

        st, err = participant_http.call_participant(
            url="http://p/y",
            phase=participant_http.PHASE_CONFIRM,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload=None,
        )
        self.assertEqual(st, 503)
        self.assertEqual(len(err), 500)
        body = mock_sync.call_args.kwargs["json_body"]
        self.assertEqual(body["payload"], {})

    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_http_error_returns_zero_status(
        self, mock_sync, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_sync.side_effect = httpx.ConnectError("refused")

        st, err = participant_http.call_participant(
            url="http://p/z",
            phase=participant_http.PHASE_CANCEL,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={},
            cancel_reason=CancelReason.DUPLICATE_CALLBACK,
        )
        self.assertEqual(st, 0)
        self.assertIn("refused", err)
        self.assertEqual(
            mock_sync.call_args.kwargs["json_body"]["cancel_reason"],
            CancelReason.DUPLICATE_CALLBACK,
        )

    @patch("app_tcc.services.participant_http.maybe_expand_service_discovery_url")
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_cancel_omits_explicit_reason_uses_unpaid(
        self, mock_sync, mock_expand
    ):
        mock_expand.side_effect = lambda u: u
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_sync.return_value = mock_resp
        participant_http.call_participant(
            url="http://p/c",
            phase=participant_http.PHASE_CANCEL,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={},
        )
        self.assertEqual(
            mock_sync.call_args.kwargs["json_body"]["cancel_reason"],
            0,
        )

    def test_is_success_status(self):
        self.assertTrue(participant_http.is_success_status(200))
        self.assertTrue(participant_http.is_success_status(299))
        self.assertFalse(participant_http.is_success_status(199))
        self.assertFalse(participant_http.is_success_status(300))
        self.assertFalse(participant_http.is_success_status(0))
