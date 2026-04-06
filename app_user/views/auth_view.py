from rest_framework.views import APIView

from app_user.services import AuthService
from app_user.utils.auth_context import client_ip_from_request
from common.consts.response_const import (
    RET_INVALID_PARAM,
    RET_UNAUTHORIZED,
    RET_TOKEN_INVALID,
)
from common.exceptions.base_exception import CheckedException
from common.utils.http_util import resp_ok, resp_err


class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            payload = dict(data)
            if hasattr(request, "FILES") and request.FILES.get("avatar"):
                payload["avatar"] = request.FILES.get("avatar")
            return resp_ok(AuthService.register_request_by_payload(payload))
        except CheckedException as exc:
            return resp_err(
                data=exc.data,
                code=exc.ret_code,
                message=exc.message,
                detail=exc.detail,
                status=exc.http_status,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class RegisterVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.register_verify_by_payload(data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            result = AuthService.login(
                login_key=(data.get("login_key") or "").strip(),
                password=data.get("password") or "",
                client_ip=client_ip_from_request(request),
            )
            return resp_ok(result)
        except CheckedException as exc:
            return resp_err(
                data=exc.data,
                code=exc.ret_code,
                message=exc.message,
                detail=exc.detail,
                status=exc.http_status,
            )
        except ValueError as exc:
            return resp_err(code=RET_UNAUTHORIZED, message=str(exc))

    def put(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            result = AuthService.refresh(refresh_token=(data.get("refresh_token") or "").strip())
            return resp_ok(result)
        except CheckedException as exc:
            return resp_err(
                data=exc.data,
                code=exc.ret_code,
                message=exc.message,
                detail=exc.detail,
                status=exc.http_status,
            )
        except ValueError as exc:
            return resp_err(code=RET_TOKEN_INVALID, message=str(exc))


class PasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.request_password_reset_by_payload(data))
        except CheckedException as exc:
            return resp_err(
                data=exc.data,
                code=exc.ret_code,
                message=exc.message,
                detail=exc.detail,
                status=exc.http_status,
            )
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))


class PasswordResetVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data if hasattr(request, "data") else request.POST
        try:
            return resp_ok(AuthService.verify_password_reset_by_payload(data))
        except ValueError as exc:
            return resp_err(code=RET_INVALID_PARAM, message=str(exc))
