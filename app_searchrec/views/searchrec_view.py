from rest_framework.views import APIView

from app_searchrec.repos.reg_repo import get_reg_by_access_key_and_status
from app_searchrec.services import SearchRecService
from common.consts.response_const import RET_INVALID_PARAM
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.http_util import (
    post_payload,
    resolve_request_id,
    resp_err,
    resp_ok,
    response_with_request_id,
)
from common.utils.type_util import as_dict, as_list


def _strategy_param(raw):
    if raw is None or raw == "":
        return "hybrid"
    return str(raw)


def _resolve_reg_id_from_payload(data) -> int:
    if not isinstance(data, dict):
        raise ValueError("field `access_key` is required")
    access_key = (data.get("access_key") or "").strip()
    if not access_key:
        raise ValueError("field `access_key` is required")
    reg = get_reg_by_access_key_and_status(access_key, ServiceRegStatus.ENABLED)
    if not reg:
        raise ValueError("invalid or inactive access_key")
    return reg.id


class SearchRecHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return response_with_request_id(request, resp_ok({"status": "ok", "service": "searchrec"}))


class SearchRecIndexUpsertView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            reg_id = _resolve_reg_id_from_payload(data)
            return response_with_request_id(
                request,
                resp_ok(SearchRecService.upsert_documents(reg_id, data.get("documents"))),
                req_id,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)


class SearchRecSearchView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            reg_id = _resolve_reg_id_from_payload(data)
            return response_with_request_id(
                request,
                resp_ok(
                    SearchRecService.search(
                        reg_id,
                        query=str(data.get("query", "")),
                        top_k=data.get("top_k", 10),
                        preferred_tags=as_list(data.get("preferred_tags")),
                    )
                ),
                req_id,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)


class SearchRecRecommendView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            reg_id = _resolve_reg_id_from_payload(data)
            return response_with_request_id(
                request,
                resp_ok(
                    SearchRecService.recommend(
                        reg_id,
                        user_profile=as_dict(data.get("user_profile")),
                        top_k=data.get("top_k", 10),
                    )
                ),
                req_id,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)


class SearchRecRankView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            _resolve_reg_id_from_payload(data)
            return response_with_request_id(
                request,
                resp_ok(
                    SearchRecService.rank(
                        candidates=as_list(data.get("candidates")),
                        strategy=_strategy_param(data.get("strategy")),
                    )
                ),
                req_id,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)
