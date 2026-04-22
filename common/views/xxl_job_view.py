"""Shared DRF views for XXL-JOB embedded executor (beat / run / kill)."""

from __future__ import annotations

import logging

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.services.xxl_job import (
    get_registry,
    parse_run_body,
    read_access_token,
    run_sync,
    validate_token,
)
from common.services.xxl_job.response import fail, success

logger = logging.getLogger(__name__)


def _deny(request: Request) -> Response | None:
    exp = (getattr(settings, "XXL_JOB_TOKEN", "") or "").strip()
    if not exp:
        logger.error("[xxl_job] XXL_JOB_TOKEN missing")
        return Response(fail("XXL_JOB_TOKEN is not configured"), status=200)
    if not validate_token(provided=read_access_token(request), expected=exp):
        logger.warning("[xxl_job] bad token")
        return Response(fail("Token validation failed"), status=200)
    return None


class XxlJobBeatView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request, *args, **kwargs):
        err = _deny(request)
        return err if err is not None else Response(success(), status=200)


class XxlJobRunView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs):
        err = _deny(request)
        if err is not None:
            return err
        data = request.data if isinstance(request.data, dict) else None
        if data is None:
            return Response(fail("JSON object required"), status=200)
        try:
            pr = parse_run_body(data)
        except (KeyError, TypeError, ValueError) as e:
            return Response(fail(str(e) or "bad payload"), status=200)
        run_sync(
            registry=get_registry(),
            executor_handler=pr.executor_handler,
            executor_params=pr.executor_params,
            log_id=pr.log_id,
        )
        return Response(success(), status=200)


class XxlJobKillView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request, *args, **kwargs):
        err = _deny(request)
        return err if err is not None else Response(success(msg="noop"), status=200)
