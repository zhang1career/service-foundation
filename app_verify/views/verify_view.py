from rest_framework.views import APIView

from app_verify.services import VerifyService
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import post_payload, resp_ok, resp_err


class VerifyRequestView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        try:
            return resp_ok(VerifyService.request_code_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class VerifyCheckView(APIView):
    def post(self, request, *args, **kwargs):
        data = post_payload(request)
        try:
            return resp_ok(VerifyService.verify_code_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
