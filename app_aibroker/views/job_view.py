from rest_framework.views import APIView

from app_aibroker.repos import get_job_by_id
from app_aibroker.services.auth_service import resolve_reg
from app_aibroker.services.job_service import enqueue_job, job_to_dict
from common.consts.response_const import RET_INVALID_PARAM, RET_UNAUTHORIZED
from common.utils.http_util import resp_ok, resp_err


class JobCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = dict(request.data) if hasattr(request, "data") else {}
        reg, errmsg = resolve_reg(data, getattr(request, "headers", {}))
        if not reg:
            return resp_err(code=RET_UNAUTHORIZED, message=errmsg)
        inner = {k: v for k, v in data.items() if k != "access_key"}
        job_type = (inner.get("job_type") or "").strip()
        if not job_type:
            return resp_err(code=RET_INVALID_PARAM, message="job_type is required")
        payload = inner.get("payload") or {}
        if not isinstance(payload, dict):
            return resp_err(code=RET_INVALID_PARAM, message="payload must be an object")
        callback_url = (inner.get("callback_url") or "").strip()
        try:
            return resp_ok(enqueue_job(reg.id, job_type, payload, callback_url))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class JobDetailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, job_id, *args, **kwargs):
        payload = {"access_key": (request.query_params.get("access_key") or "").strip()}
        reg, errmsg = resolve_reg(payload, getattr(request, "headers", {}))
        if not reg:
            return resp_err(code=RET_UNAUTHORIZED, message=errmsg)
        jid = int(job_id)
        job = get_job_by_id(jid)
        if not job or job.reg_id != reg.id:
            return resp_err(code=RET_INVALID_PARAM, message="job not found")
        return resp_ok(job_to_dict(job))
