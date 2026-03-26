from rest_framework.views import APIView

from app_aibroker.services.template_admin_service import TemplateAdminService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, with_type


class TemplateListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        key = (request.query_params.get("template_key") or "").strip() or None
        return resp_ok({"data": TemplateAdminService.list_all(key)})

    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(TemplateAdminService.create_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class TemplateDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, template_id, *args, **kwargs):
        try:
            return resp_ok(TemplateAdminService.get_one(with_type(template_id)))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)

    def patch(self, request, template_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(TemplateAdminService.update_by_payload(with_type(template_id), data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)

    def delete(self, request, template_id, *args, **kwargs):
        try:
            TemplateAdminService.delete(with_type(template_id))
            return resp_ok({"deleted": True})
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
