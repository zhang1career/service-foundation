from rest_framework.views import APIView

from common.utils.http_util import resp_ok


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return resp_ok({"status": "ok", "service": "app_aibroker"})
