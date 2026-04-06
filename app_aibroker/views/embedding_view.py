from rest_framework.views import APIView

from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.embedding_generation_service import embed_text
from common.consts.response_const import RET_AI_ERROR, RET_UNAUTHORIZED
from common.utils.http_util import resp_ok, resp_err


class EmbeddingCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = dict(request.data) if hasattr(request, "data") else {}
        reg, errmsg = resolve_reg(data, getattr(request, "headers", {}))
        if not reg:
            return resp_err(code=RET_UNAUTHORIZED, message=errmsg)
        inner = {k: v for k, v in data.items() if k != "access_key"}
        result, gen_err, err_code = embed_text(reg, inner)
        if gen_err:
            return resp_err(code=err_code if err_code is not None else RET_AI_ERROR, message=gen_err)
        return resp_ok(result)
