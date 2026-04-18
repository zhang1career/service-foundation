"""HTTP API: resolve config by access_key, key, conditions (with server-side cache)."""

import json

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
from common.annotations import http_response_client_cache
from common.consts.response_const import RET_INVALID_PARAM
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.http_util import (
    post_payload,
    resolve_request_id,
    resp_err,
    resp_ok,
    response_with_request_id,
)

# Pub/pri: caller access key MUST be sent as X-Config-Access-Key (not URL or JSON body),
# so it is less likely to appear in access logs, proxies, or Referer.
CONFIG_PUB_ACCESS_KEY_HEADER = "X-Config-Access-Key"
CONFIG_PUB_CONFIG_KEY_HEADER = "X-Config-Key"


def _header_config_access_key(request) -> str:
    headers = getattr(request, "headers", None)
    if headers is not None:
        return (headers.get(CONFIG_PUB_ACCESS_KEY_HEADER) or "").strip()
    return (request.META.get("HTTP_X_CONFIG_ACCESS_KEY") or "").strip()


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


def _pub_headers_access_key_and_config_key(request) -> tuple[str, str]:
    access_key = _header_config_access_key(request)
    headers = getattr(request, "headers", None)
    if headers is not None:
        key = (headers.get(CONFIG_PUB_CONFIG_KEY_HEADER) or "").strip()
    else:
        key = (request.META.get("HTTP_X_CONFIG_KEY") or "").strip()
    return access_key, key


def _pub_query_params_payload(request) -> dict:
    qp = getattr(request, "query_params", request.GET)
    access_key, key = _pub_headers_access_key_and_config_key(request)
    out: dict = {"access_key": access_key, "key": key}
    raw = qp.get("conditions")
    if raw is not None and str(raw).strip() != "":
        try:
            out["conditions"] = json.loads(str(raw))
        except json.JSONDecodeError:
            raise ValueError("conditions must be valid JSON") from None
    return out


def _pri_post_payload(request) -> dict:
    raw = post_payload(request)
    if isinstance(raw, dict):
        body = dict(raw)
    else:
        try:
            body = dict(raw)
        except (TypeError, ValueError):
            raise ValueError("invalid payload") from None
    body.pop("access_key", None)
    body["access_key"] = _header_config_access_key(request)
    return body


def _execute_config_query(request, data: dict, endpoint_mode: str):
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


def _execute_config_post(request, endpoint_mode: str):
    if endpoint_mode != "pri":
        return _execute_config_query(request, post_payload(request), endpoint_mode)
    try:
        data = _pri_post_payload(request)
    except ValueError as exc:
        req_id = resolve_request_id(request)
        return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)
    return _execute_config_query(request, data, endpoint_mode)


class ConfigHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return response_with_request_id(request, resp_ok({"status": "ok", "service": "config"}))


class ConfigPubQueryView(APIView):
    """
    GET:
      `X-Config-Access-Key` + `X-Config-Key` headers;
      optional `conditions` query (JSON string).
      No login;
      only ``public=1`` rows.
    """

    authentication_classes = ()
    permission_classes = ()

    @http_response_client_cache(300)
    def get(self, request, *args, **kwargs):
        try:
            data = _pub_query_params_payload(request)
        except ValueError as exc:
            req_id = resolve_request_id(request)
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)
        return _execute_config_query(request, data, "pub")


class ConfigPriQueryView(APIView):
    """
    POST JSON:
      `X-Config-Access-Key` header required.
      `key`,
      optional `conditions`.
      Login required;
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return _execute_config_post(request, "pri")
