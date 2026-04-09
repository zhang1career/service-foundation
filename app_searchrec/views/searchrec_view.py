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
        rid = resolve_request_id(request)
        try:
            return _with_request_id(request, resp_ok(SearchRecService.upsert_documents(data.get("documents"))), rid)
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=rid)


class SearchRecSearchView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        rid = resolve_request_id(request)
        try:
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.search(
                        query=str(data.get("query", "")),
                        top_k=data.get("top_k", 10),
                        preferred_tags=_optional_list(data.get("preferred_tags")),
                    )
                ),
                rid,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=rid)


class SearchRecRecommendView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        rid = resolve_request_id(request)
        try:
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.recommend(
                        user_profile=_optional_dict(data.get("user_profile")),
                        top_k=data.get("top_k", 10),
                    )
                ),
                rid,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=rid)


class SearchRecRankView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        rid = resolve_request_id(request)
        try:
            return _with_request_id(
                request,
                resp_ok(
                    SearchRecService.rank(
                        candidates=_optional_list(data.get("candidates")),
                        strategy=_strategy_param(data.get("strategy")),
                    )
                ),
                rid,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc), req_id=rid)
