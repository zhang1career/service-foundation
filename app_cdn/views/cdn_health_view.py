from rest_framework.views import APIView

from common.utils.http_util import resp_ok, response_with_request_id


class CdnHealthView(APIView):
    def get(self, request, *args, **kwargs):
        return response_with_request_id(request, resp_ok({"status": "ok", "service": "cdn"}))
