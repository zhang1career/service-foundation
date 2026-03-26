from rest_framework.views import APIView

from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.metrics_service import summary_since
from common.consts.response_const import RET_UNAUTHORIZED
from common.utils.http_util import resp_ok, resp_err, with_type


class MetricsSummaryView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        data = {"access_key": (request.query_params.get("access_key") or "").strip()}
        reg, err = resolve_reg(data, getattr(request, "headers", {}))
        if not reg:
            return resp_err(err, code=RET_UNAUTHORIZED)
        raw_w = request.query_params.get("window_ms")
        window_ms = int(with_type(raw_w)) if raw_w not in (None, "") else 86400000
        return resp_ok(summary_since(reg_id=reg.id, window_ms=window_ms))
