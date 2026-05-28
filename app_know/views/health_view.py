from rest_framework.views import APIView

from app_know.services.graphiti_client import GraphitiClient
from common.utils.http_util import resp_ok, response_with_request_id


class KnowHealthView(APIView):
    def get(self, request, *args, **kwargs):
        graphiti_ok = True
        try:
            GraphitiClient().healthcheck()
        except Exception:
            graphiti_ok = False
        return response_with_request_id(
            request,
            resp_ok({"status": "ok", "service": "know", "graphiti": "ok" if graphiti_ok else "down"}),
        )
