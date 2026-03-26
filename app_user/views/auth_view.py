from rest_framework.views import APIView

from common.consts.response_const import RET_INVALID_PARAM, RET_UNAUTHORIZED, RET_TOKEN_INVALID
from common.utils.http_util import resp_ok, resp_err
from app_user.services import AuthService

class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            payload = dict(data)
            if hasattr(request, "FILES") and request.FILES.get("avatar"):
                payload["avatar"] = request.FILES.get("avatar")
            return resp_ok(AuthService.register_request_by_payload(payload))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class RegisterVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.register_verify_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            result = AuthService.login(
                login_key=(data.get("login_key") or "").strip(),
                password=data.get("password") or "",
            )
            return resp_ok(result)
        except ValueError as exc:
            return resp_err(str(exc), code=RET_UNAUTHORIZED)


class RefreshView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            result = AuthService.refresh(refresh_token=(data.get("refresh_token") or "").strip())
            return resp_ok(result)
        except ValueError as exc:
            return resp_err(str(exc), code=RET_TOKEN_INVALID)


class PasswordResetRequestView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.request_password_reset_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)


class PasswordResetVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.verify_password_reset_by_payload(data))
        except ValueError as exc:
            return resp_err(str(exc), code=RET_INVALID_PARAM)
