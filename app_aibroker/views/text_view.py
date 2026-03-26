from rest_framework.views import APIView

from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.text_generation_service import generate_text
from common.consts.response_const import RET_UNAUTHORIZED, RET_AI_ERROR, RET_IDEMPOTENT_CONFLICT
from common.utils.http_util import resp_ok, resp_err


class TextGenerateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = dict(request.data) if hasattr(request, "data") else {}
        reg, err = resolve_reg(data, getattr(request, "headers", {}))
        if not reg:
            return resp_err(err, code=RET_UNAUTHORIZED)

        idem = (request.headers.get("Idempotency-Key") or "").strip() or None
        inner = {k: v for k, v in data.items() if k != "access_key"}
        result, gen_err = generate_text(reg, inner, idempotency_key=idem)
        if gen_err == "idempotency key reused with different payload":
            return resp_err(gen_err, code=RET_IDEMPOTENT_CONFLICT)
        if gen_err:
            return resp_err(gen_err, code=RET_AI_ERROR)
        return resp_ok(result)
