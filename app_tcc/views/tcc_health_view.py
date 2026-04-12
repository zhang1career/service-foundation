from rest_framework.views import APIView

from common.utils.http_util import resp_ok


class TccHealthView(APIView):
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        return resp_ok({"status": "ok", "service": "tcc"})
