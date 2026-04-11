"""HTTP API for keepcon (health + internal message dispatch)."""

from rest_framework.views import APIView

from app_keepcon.repos.reg_repo import get_reg_by_access_key_and_status
from app_keepcon.services.dispatch_service import dispatch_to_device
from common.consts.response_const import RET_INVALID_PARAM
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.http_util import (
    post_payload,
    resolve_request_id,
    resp_err,
    resp_ok,
    response_with_request_id,
)


class KeepconHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return response_with_request_id(request, resp_ok({"status": "ok", "service": "keepcon"}))


class KeepconInternalDispatchView(APIView):
    """POST JSON: access_key (caller reg), device_key, payload, idem_key (optional, alias idempotency_key)."""

    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            access_key = (data.get("access_key") or "").strip()
            if not access_key:
                raise ValueError("access_key is required")
            if not get_reg_by_access_key_and_status(access_key, ServiceRegStatus.ENABLED):
                raise ValueError("invalid or inactive access_key")
            device_key = (data.get("device_key") or "").strip()
            if not device_key:
                raise ValueError("device_key is required")
            if "payload" not in data:
                raise ValueError("payload is required")
            payload = data.get("payload")
            idem = data.get("idem_key")
            if idem is None:
                idem = data.get("idempotency_key")
            if idem is None or (isinstance(idem, str) and not idem.strip()):
                idem_key = None
            else:
                idem_key = str(idem).strip()
            result = dispatch_to_device(device_key, payload, idem_key)
            return response_with_request_id(request, resp_ok(result), req_id)
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)
