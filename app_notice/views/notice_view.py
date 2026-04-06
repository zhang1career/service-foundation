from rest_framework.views import APIView

from app_notice.services import enqueue_notice_by_payload
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err


class NoticeSendView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(enqueue_notice_by_payload(data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
