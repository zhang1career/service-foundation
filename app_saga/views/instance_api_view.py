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
            raw_ik = data.get("idem_key")
            if raw_ik is not None:
                try:
                    idem_key = int(raw_ik)
                except (TypeError, ValueError):
                    return resp_err(code=RET_INVALID_PARAM, message="idem_key must be int")
            else:
                hdr = (request.headers.get("X-Request-Id") or "").strip()
                if hdr:
                    try:
                        idem_key = int(hdr)
                    except (TypeError, ValueError):
                        return resp_err(
                            code=RET_INVALID_PARAM, message="X-Request-Id must be int"
                        )
                else:
                    idem_key = 0
            tcc_tok = data.get("tcc_access_key")
            if tcc_tok is not None and not isinstance(tcc_tok, str):
                return resp_err(
                    code=RET_INVALID_PARAM, message="tcc_access_key must be string"
                )
            out = saga_coordinator.start_instance(
                access_key=access_key.strip(),
                flow_id=flow_id,
                context=ctx,
                idem_key=idem_key,
                step_payloads=step_payloads,
                tcc_access_key=tcc_tok,
            )
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class SagaInstanceDetailView(APIView):
    authentication_classes = []

    def get(self, request, instance_id: str, *args, **kwargs):
        raw = (instance_id or "").strip()
        if not raw:
            return resp_err(code=RET_INVALID_PARAM, message="instance_id required")
        try:
            pk = int(raw)
        except (TypeError, ValueError):
            return resp_err(code=RET_INVALID_PARAM, message="instance_id must be int")
        inst = saga_coordinator.get_instance_by_id(pk)
        if not inst:
            return resp_err(code=RET_INVALID_PARAM, message="instance not found")
        return resp_ok(saga_coordinator.serialize_instance(inst))
