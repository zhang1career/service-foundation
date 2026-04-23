"""
XXL-JOB executor contract vs docker-lab job-executor (PHP reference).

Reference: job-executor returns JSON object ``{ "code", "msg", "data" }`` from
``XxlResponse::success()``; admin POST body matches XXL ``/run`` payload shape.
These tests pin the same contract for this repo and catch regressions in
response serialization / access-log summary.

Run without full project MySQL::

  DJANGO_SETTINGS_MODULE=common.tests.middleware.settings_xxl_mw_min \\
    python -m django test common.tests.middleware.test_xxl_job_executor_middleware
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from common.middleware.xxl_job_executor_middleware import (
    XxlJobExecutorLogMiddleware,
    response_payload_summary,
)
from common.services.xxl_job.response import success
from common.utils.json_util import API_JSON_DUMPS_PARAMS
from common.views.xxl_job_view import XxlJobRunView


class ResponsePayloadSummaryTests(SimpleTestCase):
    """How access-log reads bodies (DRF vs raw HttpResponse)."""

    def test_drf_response_uses_data_not_bytes(self) -> None:
        resp = Response(success(), status=200)
        code, msg, data = response_payload_summary(resp)
        self.assertEqual(code, 200)
        self.assertEqual(msg, "")
        self.assertIsNone(data)

    def test_json_response_parses_content(self) -> None:
        envelope = success()
        resp = JsonResponse(envelope, status=200, json_dumps_params=API_JSON_DUMPS_PARAMS)
        code, msg, data = response_payload_summary(resp)
        self.assertEqual(code, 200)
        self.assertEqual(msg, "")
        self.assertIsNone(data)

    def test_http_response_bytes_parse_as_xxl_object(self) -> None:
        body = json.dumps(success(), separators=(",", ":")).encode("utf-8")
        resp = HttpResponse(body, content_type="application/json", status=200)
        code, msg, data = response_payload_summary(resp)
        self.assertEqual(code, 200)
        self.assertEqual(msg, "")
        self.assertIsNone(data)


class XxlJobRunViewContractTests(SimpleTestCase):
    """Same POST shape as docker-lab XxlJobController::run + admin scheduler."""

    _ADMIN_STYLE_BODY = {
        "jobId": 10,
        "executorHandler": "tccScan",
        "executorParams": "",
        "executorBlockStrategy": "SERIAL_EXECUTION",
        "executorTimeout": 0,
        "logId": 285,
        "logDateTime": 1776878891627,
        "glueType": "BEAN",
        "glueSource": "",
        "glueUpdatetime": 1776863776000,
        "broadcastIndex": 0,
        "broadcastTotal": 1,
    }

    @override_settings(XXL_JOB_TOKEN="ref-token", XXL_JOB_ADMIN_ADDRESS="")
    @patch("common.views.xxl_job_view.run_sync")
    def test_run_view_accepts_admin_style_body_returns_xxl_envelope(
            self, mock_run_sync: MagicMock,
    ) -> None:
        mock_run_sync.return_value = (True, {"closed": 7, "errors": 0})
        factory = APIRequestFactory()
        request = factory.post(
            "/api/tcc/xxl-job/run",
            self._ADMIN_STYLE_BODY,
            format="json",
            HTTP_XXL_JOB_ACCESS_TOKEN="ref-token",
        )
        response = XxlJobRunView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        raw = response.content
        self.assertTrue(raw.startswith(b"{"), msg=raw[:120])
        parsed = json.loads(raw.decode("utf-8"))
        self.assertEqual(parsed.get("code"), 200)
        self.assertEqual(parsed.get("msg"), '{"closed":7,"errors":0}')
        self.assertIsNone(parsed.get("data"))
        mock_run_sync.assert_called_once()


class XxlJobExecutorLogMiddlewareTests(SimpleTestCase):
    def test_process_response_summary_matches_drf_xxl_envelope(self) -> None:
        mock_log = MagicMock()
        with (
            override_settings(
                XXLJOB_EXECUTOR_ACCESS_LOG=[("/api/tcc/", "test_xxl_mw.access")],
            ),
            patch(
                "common.middleware.xxl_job_executor_middleware.logging.getLogger",
                return_value=mock_log,
            ),
        ):
            mw = XxlJobExecutorLogMiddleware(lambda r: HttpResponse())
            rf = RequestFactory()
            request = rf.post("/api/tcc/xxl-job/run")
            request.path = "/api/tcc/xxl-job/run"
            mw.process_request(request)
            response = JsonResponse(
                success(), status=200, json_dumps_params=API_JSON_DUMPS_PARAMS
            )
            mw.process_response(request, response)
        self.assertEqual(mock_log.info.call_count, 2)
        _fmt, status, code, msg, data, _dur = mock_log.info.call_args_list[1].args
        self.assertEqual(status, 200)
        self.assertEqual(code, 200)
        self.assertEqual(msg, "")
        self.assertIsNone(data)
