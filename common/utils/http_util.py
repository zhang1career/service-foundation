import logging
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.http import HttpResponse, HttpResponseBase, JsonResponse
from rest_framework import status as http_status
from rest_framework.response import Response as DRFResponse
from rest_framework.views import exception_handler as drf_exception_handler

from common.consts.response_const import RET_INVALID_PARAM, RET_OK, RET_UNKNOWN
from common.exceptions.base_exception import CheckedException, UncheckedException, generic_message_for_ret
from common.exceptions.checked.upstream_http_error import UpstreamHttpError
from common.pojo.response import Response
from common.services.http import HttpCallError, request_sync
from common.utils.date_util import get_date_str_of_datetime
from common.utils.url_util import url_decode


logger = logging.getLogger(__name__)


def response_as_dict(obj: Response) -> dict:
    d = asdict(obj)
    if not d.get("_embedded"):
        del d["_embedded"]
    if not d.get("detail"):
        del d["detail"]
    if not d.get("_req_id"):
        del d["_req_id"]
    return d


def resolve_request_id(request) -> str:
    if request is None:
        return uuid.uuid4().hex[:16]
    rid = (
        getattr(request, "request_id", None)
        or request.META.get("HTTP_X_REQUEST_ID")
        or request.META.get("HTTP_X_REQUEST_ID".upper().replace("-", "_"))
    )
    if rid is not None and str(rid).strip().lower() not in ("", "none", "null"):
        return str(rid).strip()
    return uuid.uuid4().hex[:16]


def attach_request_id_header(response: HttpResponseBase, request_id: str) -> None:
    if not request_id:
        return
    header = getattr(settings, "REQUEST_ID_RESPONSE_HEADER", None) or "X-Request-Id"
    response[header] = request_id


def with_type(data):
    """
    Convert string to int, true to True, false to False

    @param data: data to convert
    @return: converted data
    """
    try:
        if isinstance(data, list):
            return [with_type(item) for item in data]
        if isinstance(data, dict):
            return {key: with_type(value) for key, value in data.items()}

        if data is None:
            return None
        if isinstance(data, (int, bool)):
            return data
        if isinstance(data, float):
            return data  # Optionally handle floats as-is
        if isinstance(data, str):
            if data.isnumeric():
                return int(data)
            if data.lower() == "true":
                return True
            if data.lower() == "false":
                return False
            return url_decode(data)

        raise TypeError(f"Unsupported data type: {type(data)}")
    except Exception as e:
        logger.error(f"Error processing data: {data}, error: {e}")
        raise


def resp_ok(data=None, status=http_status.HTTP_200_OK):
    response_obj = Response(
        errorCode=RET_OK,
        data=data,
        message="",
    )
    response = DRFResponse(response_as_dict(response_obj), status=status)
    response["Expires"] = get_date_str_of_datetime(
        (datetime.now(timezone.utc) + timedelta(seconds=5)),
        "%a, %d %b %Y %H:%M:%S %Z",
    )
    return response


def resp_warn(message):
    response_obj = Response(
        errorCode=RET_OK,
        data=None,
        message=message,
    )
    return DRFResponse(response_as_dict(response_obj), status=http_status.HTTP_200_OK)


def resp_err(message, code=-1, status=http_status.HTTP_200_OK, detail="", req_id=""):
    response_obj = Response(
        errorCode=code,
        data=None,
        message=message,
        detail=detail or "",
        _req_id=req_id or "",
    )
    response = DRFResponse(response_as_dict(response_obj), status=status)
    attach_request_id_header(response, req_id)
    return response


def resp_exception(e: Exception, code=-1, status=http_status.HTTP_200_OK, detail="", req_id=""):
    if settings.DEBUG:
        message = repr(e)
    else:
        message = str(e)
    response_obj = Response(
        errorCode=code,
        data=None,
        message=message,
        detail=detail or "",
        _req_id=req_id or "",
    )
    response = DRFResponse(response_as_dict(response_obj), status=status)
    attach_request_id_header(response, req_id)
    return response


def drf_unified_exception_handler(exc, context):
    request = context.get("request")
    request_id = resolve_request_id(request) if request else uuid.uuid4().hex[:16]

    if isinstance(exc, CheckedException):
        r = resp_err(
            exc.message,
            code=exc.ret_code,
            status=exc.http_status,
            detail=exc.detail,
            req_id=request_id,
        )
        return r

    if isinstance(exc, UncheckedException):
        detail_out = exc.detail if settings.DEBUG else ""
        logger.exception(
            "unchecked_exception %s: %s",
            type(exc).__name__,
            exc.detail,
            extra={"request_id": request_id},
        )
        return resp_err(
            generic_message_for_ret(exc.ret_code),
            code=exc.ret_code,
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_out,
            req_id=request_id,
        )

    if isinstance(exc, ValueError):
        return resp_err(
            generic_message_for_ret(RET_INVALID_PARAM),
            code=RET_INVALID_PARAM,
            status=http_status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
            req_id=request_id,
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        if request:
            attach_request_id_header(response, request_id)
        return response

    logger.exception(
        "unhandled_exception: %s",
        exc,
        extra={"request_id": request_id},
    )
    detail_out = repr(exc) if settings.DEBUG else ""
    return resp_err(
        generic_message_for_ret(RET_UNKNOWN),
        code=RET_UNKNOWN,
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail_out,
        req_id=request_id,
    )


class UnifiedExceptionMiddleware:
    """
    Last-resort for non-DRF views. APIs use REST_FRAMEWORK['EXCEPTION_HANDLER'] -> drf_unified_exception_handler.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.core.exceptions import PermissionDenied, SuspiciousOperation
        from django.http import Http404

        if isinstance(exception, (Http404, PermissionDenied, SuspiciousOperation)):
            return None

        request_id = resolve_request_id(request)

        if isinstance(exception, CheckedException):
            return self._respond(
                request,
                resp_err(
                    exception.message,
                    code=exception.ret_code,
                    status=exception.http_status,
                    detail=exception.detail,
                    req_id=request_id,
                ),
                request_id,
            )

        if isinstance(exception, UncheckedException):
            logger.exception(
                "unchecked_exception %s: %s",
                type(exception).__name__,
                exception.detail,
                extra={"request_id": request_id},
            )
            detail_out = exception.detail if settings.DEBUG else ""
            return self._respond(
                request,
                resp_err(
                    generic_message_for_ret(exception.ret_code),
                    code=exception.ret_code,
                    status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=detail_out,
                    req_id=request_id,
                ),
                request_id,
            )

        logger.exception(
            "unhandled_exception: %s",
            exception,
            extra={"request_id": request_id},
        )
        detail_out = repr(exception) if settings.DEBUG else ""
        return self._respond(
            request,
            resp_err(
                generic_message_for_ret(RET_UNKNOWN),
                code=RET_UNKNOWN,
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail_out,
                req_id=request_id,
            ),
            request_id,
        )

    def _respond(self, request, drf_response: DRFResponse, request_id: str):
        if _wants_json(request):
            resp = JsonResponse(drf_response.data, status=drf_response.status_code, json_dumps_params={"ensure_ascii": False})
            attach_request_id_header(resp, request_id)
            return resp
        msg = drf_response.data.get("message", "错误")
        detail = drf_response.data.get("detail") or ""
        if detail:
            msg = f"{msg}（{detail}）" if not settings.DEBUG else f"{msg}\n{detail}"
        text = f"{msg}\n_req_id={request_id}" if request_id else msg
        resp = HttpResponse(text, status=drf_response.status_code, content_type="text/plain; charset=utf-8")
        attach_request_id_header(resp, request_id)
        return resp


def _wants_json(request) -> bool:
    accept = request.META.get("HTTP_ACCEPT", "")
    if "application/json" in accept:
        return True
    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        return True
    if request.path.startswith("/api/"):
        return True
    return False


def get(url):
    """
    发送get请求

    @param url:
    @return: json解码后的数据
    """
    logger.debug("[get] url=%s", url)

    try:
        response = request_sync(method="GET", url=url, pool_name="thirdparty_pool")
    except HttpCallError as exc:
        raise UpstreamHttpError(f"request error: {exc}") from exc
    if response.status_code != 200:
        raise UpstreamHttpError(
            "request error, status={status}, response={response}".format(
                status=response.status_code, response=repr(response)
            )
        )
    data = response.json()
    if not data:
        return None
    return data


def post(url, data, auth_token=None):
    """
    发送post请求

    @param url:
    @param data:
    @param auth_token:
    @return: json解码后的数据
    """
    logger.debug("[post] url=%s, data=%s", url, data)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "close",
    }
    if auth_token:
        headers["Authorization"] = "Bearer " + auth_token

    try:
        response = request_sync(
            method="POST",
            url=url,
            pool_name="thirdparty_pool",
            json_body=data,
            headers=headers,
        )
    except HttpCallError as exc:
        raise UpstreamHttpError(f"request error: {exc}") from exc
    if response.status_code != 200:
        raise UpstreamHttpError(
            "request error, status={status}, response={response}".format(
                status=response.status_code, response=repr(response)
            )
        )
    data = response.json()
    if not data:
        return None
    return data
