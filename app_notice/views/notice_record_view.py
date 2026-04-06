from rest_framework.views import APIView

from app_notice.services import enqueue_resend_notice_record
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err


class NoticeRecordResendView(APIView):
    """POST: re-queue async send for notice row id (status must be 0)."""

    def post(self, request, notice_id, *args, **kwargs):
        try:
            return resp_ok(enqueue_resend_notice_record(int(notice_id)))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
