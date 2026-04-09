from rest_framework.views import APIView

from app_searchrec.services import SearchRecService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import (
    attach_request_id_header,
    post_payload,
    resolve_request_id,
    resp_err,
    resp_ok,
)


def _optional_list(value):
    if value is None or not isinstance(value, list):
        return []
    return value


def _optional_dict(value):
    if value is None or not isinstance(value, dict):
        return {}
    return value


def _strategy_param(raw):
    if raw is None or raw == "":
        return "hybrid"
    return str(raw)


def _parse_rid(data) -> int:
    if not isinstance(data, dict):
        raise ValueError("field `rid` is required")
    raw = data.get("rid")
    if raw is None:
        raise ValueError("field `rid` is required")
    try:
        rid = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("field `rid` must be a positive integer") from exc
    if rid <= 0:
        raise ValueError("field `rid` must be a positive integer")
    return rid


def _with_request_id(request, response, request_id=None):
    rid = request_id if request_id is not None else resolve_request_id(request)
    attach_request_id_header(response, rid)
    return response


class SearchRecHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return _with_request_id(request, resp_ok({"status": "ok", "service": "searchrec"}))


class SearchRecIndexUpsertView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        req_id = resolve_request_id(request)
        try:
            reg_id = _parse_rid(data)
            return _with_request_id(
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
            reg_id = _parse_rid(data)
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.search(
                        reg_id,
                        query=str(data.get("query", "")),
                        top_k=data.get("top_k", 10),
                        preferred_tags=_optional_list(data.get("preferred_tags")),
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
            reg_id = _parse_rid(data)
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.recommend(
                        reg_id,
                        user_profile=_optional_dict(data.get("user_profile")),
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
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.rank(
                        candidates=_optional_list(data.get("candidates")),
                        strategy=_strategy_param(data.get("strategy")),
                    )
                ),
                req_id,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=req_id)
