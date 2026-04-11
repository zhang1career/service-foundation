import logging

from rest_framework.views import APIView

from app_snowflake.exceptions.clock_backward_exception import ClockBackwardException
from app_snowflake.repos.reg_repo import get_reg_by_access_key_and_status
from app_snowflake.services.snowflake_service import generate_id
from common.consts.response_const import RET_INVALID_PARAM, RET_SNOWFLAKE_CLOCK_BACKWARD
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.http_util import post_payload, resp_err, resp_exception, resp_ok

logger = logging.getLogger(__name__)


class SnowflakeDetailView(APIView):
    """与 curl / 服务间调用一致：凭 body内 access_key，不绑定 Session/CSRF。"""

    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            data = post_payload(request)
            rid = _resolve_rid_from_payload(data)
            result = generate_id(rid)
            return resp_ok(result)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except ClockBackwardException as e:
            return resp_err(code=RET_SNOWFLAKE_CLOCK_BACKWARD, message=str(e))
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)


def _resolve_rid_from_payload(data) -> int:
    if not isinstance(data, dict):
        raise ValueError("JSON body with field `access_key` is required")
    access_key = (data.get("access_key") or "").strip()
    if not access_key:
        raise ValueError("field `access_key` is required")
    reg = get_reg_by_access_key_and_status(access_key, ServiceRegStatus.ENABLED)
    if not reg:
        raise ValueError("invalid or inactive access_key")
    return int(reg.id)
