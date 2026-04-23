"""XXL-JOB embedded executor: beat / run / kill.

Always respond with ``application/json`` and a root JSON **object**
``{code, msg, data}`` (never DRF content negotiation / browsable HTML), so the
admin scheduler Gson client can deserialize reliably.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from common.services.xxl_job import (
    get_registry,
    parse_run_body,
    read_access_token,
    run_sync,
    validate_token,
)
from common.services.xxl_job.response import fail, success
from common.utils.json_util import API_JSON_DUMPS_PARAMS

logger = logging.getLogger(__name__)


def _xxl_json(payload: dict) -> JsonResponse:
    return JsonResponse(payload, status=200, json_dumps_params=API_JSON_DUMPS_PARAMS)


def _deny(request: Request) -> JsonResponse | None:
    exp = (getattr(settings, "XXL_JOB_TOKEN", "") or "").strip()
    if not exp:
        logger.error("[xxl_job] XXL_JOB_TOKEN missing")
        return _xxl_json(fail("XXL_JOB_TOKEN is not configured"))
    if not validate_token(provided=read_access_token(request), expected=exp):
        logger.warning("[xxl_job] bad token")
        return _xxl_json(fail("Token validation failed"))
    return None


class XxlJobBeatView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args, **kwargs):
        err = _deny(request)
        return err if err is not None else _xxl_json(success())


class XxlJobRunView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs):
        err = _deny(request)
        if err is not None:
            return err
        data = request.data if isinstance(request.data, dict) else None
        if data is None:
            return _xxl_json(fail("JSON object required"))
        try:
            pr = parse_run_body(data)
        except (KeyError, TypeError, ValueError) as e:
            return _xxl_json(fail(str(e) or "bad payload"))
        ok, detail = run_sync(
            registry=get_registry(),
            executor_handler=pr.executor_handler,
            executor_params=pr.executor_params,
            log_id=pr.log_id,
        )
        if ok:
            return _xxl_json(success(msg=detail))
        return _xxl_json(fail(detail))


class XxlJobKillView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs):
        err = _deny(request)
        return err if err is not None else _xxl_json(success(msg="noop"))
