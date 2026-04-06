from __future__ import annotations

from typing import Any

from common.consts import response_const as rc
from common.consts.response_const import RET_RESOURCE_NOT_FOUND, RET_MISSING_PARAM, RET_OK


def generic_code_for_ret(msg: str, code_by_default: int = RET_OK) -> tuple[int, str]:
    m = msg.lower()
    if "not found" in m:
        return RET_RESOURCE_NOT_FOUND, m
    if "required" in m or "cannot be empty" in m or "missing" in m or "non-empty" in m:
        return RET_MISSING_PARAM, m
    return code_by_default, m


def generic_message_for_ret(ret_code: int) -> str:
    return _GENERIC_MESSAGES.get(ret_code, "请求处理失败")


def http_status_for_ret(ret_code: int) -> int:
    if ret_code in _RET_TO_HTTP:
        return _RET_TO_HTTP[ret_code]
    if 200 <= ret_code < 300:
        return 403
    return 400


class CheckedException(Exception):
    """
    Expected failure the client can react to (validation, missing resource, upstream 4xx, etc.).
    Exposed to the client as: generic `message` + specific `detail` + numeric `errorCode`.
    """

    def __init__(
            self,
            detail: str,
            *,
            ret_code: int = rc.RET_INVALID_PARAM,
            message: str | None = None,
            data: Any | None = None,
            http_status: int | None = None,
    ):
        super().__init__(detail)
        self.detail = detail
        self.ret_code = ret_code
        self.message = message if message is not None else generic_message_for_ret(ret_code)
        self.data = data
        self.http_status = http_status if http_status is not None else http_status_for_ret(ret_code)


class UncheckedException(Exception):
    """
    Unexpected or non-client-actionable failure (bug, misconfiguration, invariant violation).
    Log `detail`; client receives a generic message unless DEBUG.
    """

    def __init__(
            self,
            detail: str,
            *,
            ret_code: int = rc.RET_UNKNOWN,
    ):
        super().__init__(detail)
        self.detail = detail
        self.ret_code = ret_code


_GENERIC_MESSAGES: dict[int, str] = {
    rc.RET_ERR: "请求处理失败",
    rc.RET_UNKNOWN: "服务器内部错误",
    rc.RET_NOT_IMPLEMENTED: "功能暂未实现",
    rc.RET_INVALID_PARAM: "请求参数错误",
    rc.RET_MISSING_PARAM: "缺少必要参数",
    rc.RET_PARAM_FORMAT_ERROR: "参数格式错误",
    rc.RET_PARAM_OUT_OF_RANGE: "参数超出允许范围",
    rc.RET_JSON_PARSE_ERROR: "JSON 解析失败",
    rc.RET_UNAUTHORIZED: "未授权",
    rc.RET_FORBIDDEN: "禁止访问",
    rc.RET_LOGIN_REQUIRED: "需要登录",
    rc.RET_TOKEN_MISSING: "缺少令牌",
    rc.RET_TOKEN_INVALID: "令牌无效",
    rc.RET_TOKEN_EXPIRED: "令牌已过期",
    rc.RET_TOKEN_REVOKED: "令牌已失效",
    rc.RET_ACCOUNT_RESTRICTED: "账户受限",
    rc.RET_BUSINESS_ERROR: "业务处理失败",
    rc.RET_RESOURCE_NOT_FOUND: "资源不存在",
    rc.RET_RESOURCE_EXISTS: "资源已存在",
    rc.RET_INVALID_STATE: "状态不允许此操作",
    rc.RET_DUPLICATE_REQUEST: "重复请求",
    rc.RET_OPERATION_NOT_ALLOWED: "不允许执行该操作",
    rc.RET_DEPENDENCY_ERROR: "依赖服务异常",
    rc.RET_HTTP_TIMEOUT: "外部请求超时",
    rc.RET_HTTP_5XX: "外部服务错误",
    rc.RET_HTTP_RESPONSE_INVALID: "外部响应无效",
    rc.RET_MQ_ERROR: "消息队列异常",
    rc.RET_REDIS_ERROR: "缓存服务异常",
    rc.RET_THIRD_PARTY_ERROR: "第三方服务异常",
    rc.RET_DB_ERROR: "数据服务异常",
    rc.RET_DB_CONNECTION_FAILED: "数据库连接失败",
    rc.RET_DB_QUERY_FAILED: "数据库查询失败",
    rc.RET_DB_DUPLICATE_KEY: "数据冲突",
    rc.RET_DB_TRANSACTION_FAILED: "事务失败",
    rc.RET_FILE_IO_ERROR: "文件读写失败",
    rc.RET_OBJECT_STORAGE_ERROR: "对象存储异常",
    rc.RET_CONCURRENCY_ERROR: "并发冲突",
    rc.RET_LOCK_FAILED: "获取锁失败",
    rc.RET_IDEMPOTENT_CONFLICT: "幂等冲突",
    rc.RET_RATE_LIMITED: "请求过于频繁",
    rc.RET_CIRCUIT_OPEN: "服务暂时不可用",
    rc.RET_AI_ERROR: "AI 服务异常",
    rc.RET_PROMPT_PARSE_FAILED: "提示词解析失败",
    rc.RET_PLAN_GENERATION_FAILED: "执行计划生成失败",
    rc.RET_TOOL_NOT_FOUND: "工具不存在",
    rc.RET_TOOL_EXECUTION_FAILED: "工具执行失败",
    rc.RET_MODEL_RESPONSE_INVALID: "模型响应无效",
    rc.RET_AI_POLICY_VIOLATION: "内容策略限制",
    rc.RET_CONFIG_ERROR: "服务配置错误",
    rc.RET_ENV_NOT_READY: "运行环境未就绪",
    rc.RET_SERVICE_UNAVAILABLE: "服务暂不可用",
    rc.RET_DEPLOYMENT_ERROR: "部署异常",
    rc.RET_MAINTENANCE_MODE: "系统维护中",
}

_RET_TO_HTTP: dict[int, int] = {
    rc.RET_UNAUTHORIZED: 401,
    rc.RET_FORBIDDEN: 403,
    rc.RET_LOGIN_REQUIRED: 401,
    rc.RET_TOKEN_MISSING: 401,
    rc.RET_TOKEN_INVALID: 401,
    rc.RET_TOKEN_EXPIRED: 401,
    rc.RET_TOKEN_REVOKED: 401,
    rc.RET_ACCOUNT_RESTRICTED: 403,
    rc.RET_RESOURCE_NOT_FOUND: 404,
}
