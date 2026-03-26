from rest_framework.views import APIView

from app_aibroker.services.reg_service import RegService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, with_type


class RegListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return resp_ok({"data": RegService.list_all()})

    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(RegService.create_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class RegDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, reg_id, *args, **kwargs):
        try:
            return resp_ok(RegService.get_one(reg_id=with_type(reg_id)))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)

    def patch(self, request, reg_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(RegService.update_by_payload(reg_id=with_type(reg_id), payload=data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)

    def delete(self, request, reg_id, *args, **kwargs):
        try:
            RegService.delete(reg_id=with_type(reg_id))
            return resp_ok({"deleted": True})
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
