"""HTTP API: resolve config by access_key, key, conditions (with server-side cache)."""

from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app_config.repos.reg_repo import get_reg_by_access_key_and_status
from app_config.services.config_cache_service import (
    get_rid_generation,
    query_cache_get,
    query_cache_set,
)
from app_config.services.config_merge_service import (
    conditions_hash,
    merge_config_query_result,
    normalize_conditions,
)
from common.consts.response_const import RET_INVALID_PARAM
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.http_util import (
    post_payload,
    resolve_request_id,
    resp_err,
    resp_ok,
    response_with_request_id,
)


def _resolve_reg_id_from_payload(data: dict) -> int:
    if not isinstance(data, dict):
        raise ValueError("invalid payload")
    access_key = (data.get("access_key") or "").strip()
    if not access_key:
        raise ValueError("access_key is required")
    reg = get_reg_by_access_key_and_status(access_key, ServiceRegStatus.ENABLED)
    if not reg:
        raise ValueError("invalid or inactive access_key")
    return reg.id


def _execute_config_post(request, endpoint_mode: str):
    data = post_payload(request)
    req_id = resolve_request_id(request)
    try:
        reg_id = _resolve_reg_id_from_payload(data)
        config_key = (data.get("key") or "").strip()
        if not config_key:
            raise ValueError("key is required")
        conditions = normalize_conditions(data.get("conditions"))
        rid_gen = get_rid_generation(reg_id)
        ch = conditions_hash(conditions)
        cached = query_cache_get(reg_id, rid_gen, config_key, ch, endpoint_mode)
        if cached is not None:
            return response_with_request_id(request, resp_ok(cached), req_id)
        payload = merge_config_query_result(
            reg_id, config_key, conditions, endpoint_mode=endpoint_mode
        )
        query_cache_set(reg_id, rid_gen, config_key, ch, endpoint_mode, payload)
        return response_with_request_id(request, resp_ok(payload), req_id)
    except ValueError as exc:
        return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)


class ConfigHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return response_with_request_id(request, resp_ok({"status": "ok", "service": "config"}))


class ConfigPubQueryView(APIView):
    """POST JSON: access_key, key, conditions (optional). No login; only ``public=1`` rows (no condition eval)."""

    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        return _execute_config_post(request, "pub")


class ConfigPriQueryView(APIView):
    """POST JSON: access_key, key, conditions (optional). Login required; ``public=1`` + ``public=0`` rows."""

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return _execute_config_post(request, "pri")
