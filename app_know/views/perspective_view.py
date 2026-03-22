"""
Perspective: code-only constants (no DB). Returns PERSPECTIVE_TYPES for UI.
"""
from rest_framework.views import APIView

from app_know.consts import PERSPECTIVE_TYPES
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err


class PerspectiveListView(APIView):
    """GET: return perspective types as constants. POST: stub (no DB)."""

    def get(self, request):
        return resp_ok({
            "data": [{"id": v, "label": l, "type": v, "name": l} for v, l in PERSPECTIVE_TYPES],
            "total_num": len(PERSPECTIVE_TYPES),
        })

    def post(self, request):
        return resp_err("视角类型为代码常量，不支持创建", code=RET_INVALID_PARAM, status=200)
