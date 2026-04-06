from rest_framework.views import APIView

from app_aibroker.services.provider_service import ModelService, ProviderService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, with_type


class ProviderListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return resp_ok({"data": ProviderService.list_all()})

    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(ProviderService.create_by_payload(data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class ProviderDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, provider_id, *args, **kwargs):
        try:
            return resp_ok(ProviderService.get_one(with_type(provider_id)))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))

    def patch(self, request, provider_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(ProviderService.update_by_payload(with_type(provider_id), data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))

    def delete(self, request, provider_id, *args, **kwargs):
        try:
            ProviderService.delete(with_type(provider_id))
            return resp_ok({"deleted": True})
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class ModelListCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, provider_id, *args, **kwargs):
        try:
            return resp_ok({"data": ModelService.list_for_provider(with_type(provider_id))})
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))

    def post(self, request, provider_id, *args, **kwargs):
        data = dict(request.data) if hasattr(request, "data") else {}
        data["provider_id"] = with_type(provider_id)
        try:
            return resp_ok(ModelService.create_by_payload(data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class ModelDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, provider_id, model_id, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(ModelService.update(with_type(model_id), data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))

    def delete(self, request, provider_id, model_id, *args, **kwargs):
        try:
            ModelService.delete(with_type(model_id))
            return resp_ok({"deleted": True})
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
