import logging
from rest_framework.views import APIView

from app_snowflake.exceptions.clock_backward_exception import ClockBackwardException
from app_snowflake.services.snowflake_service import generate_id
from common.consts.string_const import EMPTY_STRING
from common.utils.http_util import resp_ok, with_type, resp_exception, resp_err

logger = logging.getLogger(__name__)


class SnowflakeDetailView(APIView):
    # add permission to check if user is authenticated
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # get param
            business_id = with_type(request.GET.get("bid", EMPTY_STRING))
            # query
            result = generate_id(business_id)
            # return
            return resp_ok(result)
        except ClockBackwardException as e:
            return resp_err(str(e), 1001)
        except Exception as e:
            logger.exception(e)
            return resp_exception(e)
