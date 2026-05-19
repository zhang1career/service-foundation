from __future__ import annotations

from rest_framework.views import APIView

from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import post_payload, resp_err, resp_ok, response_with_request_id

from app_textmod.services.textmod_scan_service import TextmodScanService


class TextmodScanView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request) or {}
        text = data.get("text", "")
        if text is None:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="text is required"),
            )
        if not isinstance(text, str):
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="text must be a string"),
            )
        lexicon_id = data.get("lexicon_id")
        try:
            lexicon_id_int = int(lexicon_id)
        except (TypeError, ValueError):
            lexicon_id_int = 0
        if lexicon_id_int <= 0:
            return response_with_request_id(
                request,
                resp_err(code=RET_INVALID_PARAM, message="lexicon_id is required"),
            )
        include_normalized = bool(data.get("include_normalized", False))
        try:
            out = TextmodScanService.scan(text=text, lexicon_id=lexicon_id_int)
            if not include_normalized:
                out.pop("normalized", None)
            return response_with_request_id(request, resp_ok(out))
        except ValueError as exc:
            msg = str(exc)
            code = RET_RESOURCE_NOT_FOUND if msg == "no published lexicon version" else RET_INVALID_PARAM
            return response_with_request_id(request, resp_err(code=code, message=msg))
