from rest_framework.views import APIView

from app_aibroker.services.aibroker_multipart_service import parse_meta_json
from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.text_generation_service import generate_text
from common.consts.response_const import (
    RET_AI_ERROR,
    RET_IDEMPOTENT_CONFLICT,
    RET_INVALID_PARAM,
    RET_UNAUTHORIZED,
)
from common.utils.http_util import resp_ok, resp_err


class TextGenerateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        django_request = getattr(request, "_request", request)
        content_type = (getattr(django_request, "content_type", None) or "").lower()
        idem = (request.headers.get("Idempotency-Key") or "").strip() or None

        if "multipart/form-data" in content_type:
            meta_raw = django_request.POST.get("meta")
            meta_obj, meta_err = parse_meta_json(meta_raw)
            if meta_err:
                return resp_err(code=RET_INVALID_PARAM, message=meta_err)
            if django_request.FILES:
                return resp_err(
                    code=RET_INVALID_PARAM,
                    message="files are not accepted in this endpoint; upload first and pass image URL",
                )
            reg, errmsg = resolve_reg(meta_obj, getattr(request, "headers", {}))
            if not reg:
                return resp_err(code=RET_UNAUTHORIZED, message=errmsg)
            inner = {k: v for k, v in meta_obj.items() if k != "access_key"}
            inner.pop("attachments", None)
            result, gen_err = generate_text(reg, inner, idempotency_key=idem)
        else:
            data = dict(request.data) if hasattr(request, "data") else {}
            reg, errmsg = resolve_reg(data, getattr(request, "headers", {}))
            if not reg:
                return resp_err(code=RET_UNAUTHORIZED, message=errmsg)
            inner = {k: v for k, v in data.items() if k != "access_key"}
            inner.pop("attachments", None)
            result, gen_err = generate_text(reg, inner, idempotency_key=idem)

        if gen_err == "idempotency key reused with different payload":
            return resp_err(code=RET_IDEMPOTENT_CONFLICT, message=gen_err)
        if gen_err:
            return resp_err(code=RET_AI_ERROR, message=gen_err)
        return resp_ok(result)
