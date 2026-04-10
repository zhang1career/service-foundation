"""Monitoring JSON endpoints for console async refresh and optional token export."""

import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views import View

from app_console.services.monitoring_snapshot import get_snapshot_payload


class MonitoringSnapshotView(View):
    """GET /console/api/monitoring/snapshot/ — same payload as async page refresh (same-origin)."""

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            get_snapshot_payload(),
            json_dumps_params={"ensure_ascii": False},
        )


class MonitoringJsonView(View):
    """GET /console/api/monitoring.json — requires CONSOLE_MONITORING_JSON_TOKEN."""

    def get(self, request, *args, **kwargs):
        token = (getattr(settings, "CONSOLE_MONITORING_JSON_TOKEN", "") or "").strip()
        if not token:
            return HttpResponseForbidden("CONSOLE_MONITORING_JSON_TOKEN is not configured")
        given = (request.GET.get("token") or "").strip()
        header = (request.headers.get("X-Console-Monitoring-Token") or "").strip()
        if given != token and header != token:
            return HttpResponseForbidden("invalid token")

        payload = get_snapshot_payload()
        return HttpResponse(
            json.dumps(payload, ensure_ascii=False, default=str),
            content_type="application/json; charset=utf-8",
        )
