"""Shared GET ?codes=... dict API for enum / constant metadata."""
import logging

from rest_framework.views import APIView

from common.dict_catalog import get_dict_by_codes
from common.utils.http_util import resp_err, resp_ok, with_type

logger = logging.getLogger(__name__)


class DictCodesView(APIView):
    """GET: Query param codes (comma-separated). Returns { code: [ {k,v}, ... ] }."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        try:
            codes = with_type(request.GET.get("codes", ""))
            if not codes or not str(codes).strip():
                return resp_err("codes is required", code=400)
            result = get_dict_by_codes(str(codes).strip())
            return resp_ok(result)
        except Exception as e:
            logger.exception("[DictCodesView] Error: %s", e)
            return resp_err(str(e), code=500)
