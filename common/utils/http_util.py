import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from rest_framework import status as http_status
from rest_framework.response import Response as DRFResponse

from common.consts.response_const import RET_OK
from common.exceptions.http_exception import HttpException
from common.pojo.response import Response as Response
from common.utils.date_util import get_date_str_of_datetime
from common.utils.url_util import url_decode


logger = logging.getLogger(__name__)


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


def resp_ok(data=None):
    response_obj = Response(
        errorCode=RET_OK,
        data=data,
        message=""
    )
    response = DRFResponse(asdict(response_obj), status=http_status.HTTP_200_OK)
    response["Expires"] = get_date_str_of_datetime((datetime.now(timezone.utc) + timedelta(seconds=5)),
                                                   "%a, %d %b %Y %H:%M:%S %Z")
    return response


def resp_warn(message):
    response_obj = Response(
        errorCode=RET_OK,
        data=None,
        message=message
    )
    return DRFResponse(asdict(response_obj), status=http_status.HTTP_200_OK)


def resp_err(message, code=-1, status=http_status.HTTP_200_OK):
    response_obj = Response(
        errorCode=code,
        data=None,
        message=message
    )
    return DRFResponse(asdict(response_obj), status=status)


def resp_exception(e: Exception, code=-1, status=http_status.HTTP_200_OK):
    if settings.DEBUG:
        message = repr(e)
    else:
        message = str(e)
    response_obj = Response(
        errorCode=code,
        data=None,
        message=message
    )
    return DRFResponse(asdict(response_obj), status=status)


def get(url):
    """
    发送get请求

    @param url:
    @return: json解码后的数据
    """
    logger.debug("[get] url=%s", url)

    response = requests.get(url)
    if response.status_code != 200:
        raise HttpException("request error, status={status}, response={response}"
                            .format(status=response.status_code, response=response.__repr__))
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

    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        raise HttpException("request error, status={status}, response={response}"
                            .format(status=response.status_code, response=response.__repr__))
    data = response.json()
    if not data:
        return None
    return data
