import logging

from rest_framework.views import APIView

from app_tcc.services import coordinator
from app_tcc.services.snowflake_id import SnowflakeIdError
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import post_payload, resp_err, resp_exception, resp_ok

logger = logging.getLogger(__name__)


class TccTransactionBeginView(APIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            data = post_payload(request)
            if not isinstance(data, dict):
                return resp_err(code=RET_INVALID_PARAM, message="JSON object required")
            branches = data.get("branches")
            if not isinstance(branches, list) or not branches:
                return resp_err(code=RET_INVALID_PARAM, message="branches[] required")
            auto_confirm = data.get("auto_confirm")
            if auto_confirm is not None and not isinstance(auto_confirm, bool):
                return resp_err(code=RET_INVALID_PARAM, message="auto_confirm must be boolean")
            ctx = data.get("context")
            if ctx is not None and not isinstance(ctx, dict):
                return resp_err(code=RET_INVALID_PARAM, message="context must be object")
            out = coordinator.begin_transaction(
                branch_items=branches,
                auto_confirm=auto_confirm,
                context=ctx,
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

    def post(self, request, global_tx_id: str, *args, **kwargs):
        try:
            out = coordinator.confirm_transaction(global_tx_id.strip())
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class TccTransactionCancelView(APIView):
    authentication_classes = []

    def post(self, request, global_tx_id: str, *args, **kwargs):
        try:
            out = coordinator.cancel_transaction(global_tx_id.strip())
            return resp_ok(out)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


class TccTransactionDetailView(APIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        qp = request.query_params
        has_idem = "idem_key" in qp
        has_gtx = "global_tx_id" in qp
        if has_idem and has_gtx:
            return resp_err(
                code=RET_INVALID_PARAM,
                message="use only one of idem_key, global_tx_id",
            )
        if not has_idem and not has_gtx:
            return resp_err(
                code=RET_INVALID_PARAM,
                message="idem_key or global_tx_id required",
            )
        idem_key: int | None = None
        global_tx_id: str | None = None
        if has_idem:
            try:
                idem_key = int(qp.get("idem_key"))
            except (TypeError, ValueError):
                return resp_err(code=RET_INVALID_PARAM, message="idem_key must be int")
        else:
            global_tx_id = (qp.get("global_tx_id") or "").strip()
        g = coordinator.get_transaction_for_query(
            global_tx_id=global_tx_id,
            idem_key=idem_key,
        )
        if not g:
            return resp_err(code=RET_INVALID_PARAM, message="transaction not found")
        return resp_ok(coordinator.serialize_transaction(g))
