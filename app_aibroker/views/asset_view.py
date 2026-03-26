from rest_framework.views import APIView

from app_aibroker.services.asset_admin_service import AssetAdminService
from app_aibroker.services.auth_service import resolve_reg
from common.consts.response_const import RET_INVALID_PARAM, RET_UNAUTHORIZED
from common.utils.http_util import resp_ok, resp_err, with_type


class AssetCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = dict(request.data) if hasattr(request, "data") else {}
        reg, err = resolve_reg(data, getattr(request, "headers", {}))
        if not reg:
            return resp_err(err, code=RET_UNAUTHORIZED)
        inner = {k: v for k, v in data.items() if k != "access_key"}
        try:
            return resp_ok(AssetAdminService.create_for_reg(reg.id, inner))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class AssetDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, asset_id, *args, **kwargs):
        payload = {"access_key": (request.query_params.get("access_key") or "").strip()}
        reg, err = resolve_reg(payload, getattr(request, "headers", {}))
        if not reg:
            return resp_err(err, code=RET_UNAUTHORIZED)
        try:
            return resp_ok(AssetAdminService.get_one(with_type(asset_id), reg.id))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
