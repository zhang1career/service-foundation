import logging

from rest_framework.views import APIView

from app_tcc.enums import CANCEL_REASON_VALUES
from app_tcc.services import coordinator
from app_tcc.services.snowflake_id import SnowflakeIdError
from app_tcc.services.tx_begin_request import parse_tcc_tx_post_json
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import post_payload, resp_err, resp_exception, resp_ok

logger = logging.getLogger(__name__)


def _parse_path_idem_key(raw: str | None) -> int:
    s = (raw or "").strip()
    if not s:
        raise ValueError("idem_key required")
    try:
        return int(s)
    except ValueError:
        raise ValueError("idem_key must be a decimal integer string")


class TccTransactionBeginView(APIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            data = post_payload(request)
            if not isinstance(data, dict):
                return resp_err(code=RET_INVALID_PARAM, message="JSON object required")
            inp = parse_tcc_tx_post_json(data)
            raw_xr = request.META.get("HTTP_X_REQUEST_ID")
            if raw_xr is None:
                x_request_id = None
            else:
                x_request_id = str(raw_xr).strip() or None
            out = coordinator.begin_transaction(
                biz_id=inp.biz_id,
                branch_items=inp.branch_items,
                auto_confirm=inp.auto_confirm,
                context=inp.context,
                x_request_id=x_request_id,
            )
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except SnowflakeIdError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class TccTransactionConfirmView(APIView):
    authentication_classes = []

    def post(self, request, idem_key: str, *args, **kwargs):
        try:
            ik = _parse_path_idem_key(idem_key)
            out = coordinator.confirm_transaction(ik)
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class TccTransactionCancelView(APIView):
    authentication_classes = []

    def post(self, request, idem_key: str, *args, **kwargs):
        try:
            ik = _parse_path_idem_key(idem_key)
            data = post_payload(request)
            if not isinstance(data, dict):
                return resp_err(code=RET_INVALID_PARAM, message="JSON object required")
            if "cancel_reason" not in data:
                return resp_err(code=RET_INVALID_PARAM, message="cancel_reason required")
            try:
                cancel_reason = int(data.get("cancel_reason"))
            except (TypeError, ValueError):
                return resp_err(code=RET_INVALID_PARAM, message="cancel_reason must be int")
            if cancel_reason not in CANCEL_REASON_VALUES:
                return resp_err(code=RET_INVALID_PARAM, message="invalid cancel_reason")
            out = coordinator.cancel_transaction(ik, cancel_reason)
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class TccTransactionDetailView(APIView):
    authentication_classes = []

    def get(self, request, idem_key: str, *args, **kwargs):
        try:
            ik = _parse_path_idem_key(idem_key)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        g = coordinator.get_transaction_for_query(global_tx_id=None, idem_key=ik)
        if not g:
            return resp_err(code=RET_INVALID_PARAM, message="transaction not found")
        try:
            return resp_ok(coordinator.serialize_transaction(g))
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
