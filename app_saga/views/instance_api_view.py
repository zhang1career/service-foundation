import logging

from rest_framework.views import APIView

from app_saga.services import saga_coordinator
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import post_payload, resp_err, resp_exception, resp_ok

logger = logging.getLogger(__name__)


class SagaInstanceStartView(APIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            data = post_payload(request)
            if not isinstance(data, dict):
                return resp_err(code=RET_INVALID_PARAM, message="JSON object required")
            access_key = data.get("access_key")
            flow_id = data.get("flow_id")
            if not isinstance(access_key, str) or not access_key.strip():
                return resp_err(code=RET_INVALID_PARAM, message="access_key required")
            try:
                flow_id = int(flow_id)
            except (TypeError, ValueError):
                return resp_err(code=RET_INVALID_PARAM, message="flow_id must be int")
            ctx = data.get("context")
            if ctx is not None and not isinstance(ctx, dict):
                return resp_err(code=RET_INVALID_PARAM, message="context must be object")
            step_payloads = data.get("step_payloads")
            if step_payloads is not None and not isinstance(step_payloads, dict):
                return resp_err(code=RET_INVALID_PARAM, message="step_payloads must be object")
            idem_key = data.get("idem_key")
            if idem_key is not None:
                try:
                    idem_key = int(idem_key)
                except (TypeError, ValueError):
                    return resp_err(code=RET_INVALID_PARAM, message="idem_key must be int")
            out = saga_coordinator.start_instance(
                access_key=access_key.strip(),
                flow_id=flow_id,
                context=ctx,
                idem_key=idem_key,
                step_payloads=step_payloads,
            )
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class SagaInstanceDetailView(APIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        qp = request.query_params
        has_idem = "idem_key" in qp
        has_sid = "saga_instance_id" in qp
        if has_idem and has_sid:
            return resp_err(
                code=RET_INVALID_PARAM,
                message="use only one of idem_key, saga_instance_id",
            )
        if not has_idem and not has_sid:
            return resp_err(
                code=RET_INVALID_PARAM,
                message="idem_key or saga_instance_id required",
            )
        if has_idem:
            try:
                ik = int(qp.get("idem_key"))
            except (TypeError, ValueError):
                return resp_err(code=RET_INVALID_PARAM, message="idem_key must be int")
            inst = saga_coordinator.get_instance_by_idem(ik)
        else:
            raw = (qp.get("saga_instance_id") or "").strip()
            try:
                pk = int(raw)
            except ValueError:
                return resp_err(code=RET_INVALID_PARAM, message="saga_instance_id must be int")
            inst = saga_coordinator.get_instance_by_id(pk)
        if not inst:
            return resp_err(code=RET_INVALID_PARAM, message="instance not found")
        return resp_ok(saga_coordinator.serialize_instance(inst))
