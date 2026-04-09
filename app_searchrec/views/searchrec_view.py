from rest_framework.views import APIView

from app_searchrec.services import SearchRecService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_err, resp_ok


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


class SearchRecHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return resp_ok({"status": "ok", "service": "searchrec"})


class SearchRecIndexUpsertView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(SearchRecService.upsert_documents(data.get("documents")))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class SearchRecSearchView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.search(
                    query=str(data.get("query", "")),
                    top_k=data.get("top_k", 10),
                    preferred_tags=_optional_list(data.get("preferred_tags")),
                )
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class SearchRecRecommendView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.recommend(
                    user_profile=_optional_dict(data.get("user_profile")),
                    top_k=data.get("top_k", 10),
                )
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class SearchRecRankView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.rank(
                    candidates=_optional_list(data.get("candidates")),
                    strategy=_strategy_param(data.get("strategy")),
                )
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
