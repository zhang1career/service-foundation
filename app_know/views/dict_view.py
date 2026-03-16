"""
字典查询接口：GET ?codes=classification,source_type
返回 { "classification": [{ "k": "Claim", "v": "claim" }, ...], ... }
"""
import logging

from rest_framework.views import APIView

from app_know.services.dict_service import get_dict_by_codes
from common.utils.http_util import resp_ok, resp_err, with_type

logger = logging.getLogger(__name__)


class DictView(APIView):
    """GET: 字典查询。Query param: codes，逗号分隔的字典项名称。"""

    def get(self, request, *args, **kwargs):
        try:
            codes = with_type(request.GET.get("codes", ""))
            if not codes or not str(codes).strip():
                return resp_err("codes is required", code=400)
            result = get_dict_by_codes(str(codes).strip())
            return resp_ok(result)
        except Exception as e:
            logger.exception("[DictView] Error: %s", e)
            return resp_err(str(e), code=500)
