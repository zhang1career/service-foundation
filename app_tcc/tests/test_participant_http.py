"""Unit tests for participant HTTP client (no outbound I/O)."""

from unittest.mock import MagicMock, patch

import httpx
from django.test import SimpleTestCase, override_settings

from app_tcc.services import participant_http


@override_settings(TCC_OUTBOUND_TIMEOUT_SEC=12.0)
class ParticipantHttpTests(SimpleTestCase):
    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_success_returns_empty_error(self, mock_sync):
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

    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_failure_returns_snippet(self, mock_sync):
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

    @patch("app_tcc.services.participant_http.request_sync")
    def test_call_participant_http_error_returns_zero_status(self, mock_sync):
        mock_sync.side_effect = httpx.ConnectError("refused")

        st, err = participant_http.call_participant(
            url="http://p/z",
            phase=participant_http.PHASE_CANCEL,
            global_tx_id="1",
            branch_id="2",
            idempotency_key="k",
            payload={},
        )
        self.assertEqual(st, 0)
        self.assertIn("refused", err)

    def test_is_success_status(self):
        self.assertTrue(participant_http.is_success_status(200))
        self.assertTrue(participant_http.is_success_status(299))
        self.assertFalse(participant_http.is_success_status(199))
        self.assertFalse(participant_http.is_success_status(300))
        self.assertFalse(participant_http.is_success_status(0))
