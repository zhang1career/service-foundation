from rest_framework.views import APIView

from app_searchrec.services import SearchRecService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_err, resp_ok


class SearchRecHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return resp_ok({"status": "ok", "service": "searchrec"})


class SearchRecIndexUpsertView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(SearchRecService.upsert_documents(data.get("documents")))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class SearchRecSearchView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.search(
                    query=str(data.get("query", "")),
                    top_k=data.get("top_k", 10),
                    preferred_tags=data.get("preferred_tags") or [],
                )
            )
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class SearchRecRecommendView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.recommend(
                    user_profile=data.get("user_profile") or {},
                    top_k=data.get("top_k", 10),
                )
            )
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class SearchRecRankView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(
                SearchRecService.rank(
                    candidates=data.get("candidates") or [],
                    strategy=str(data.get("strategy") or "hybrid"),
                )
            )
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
