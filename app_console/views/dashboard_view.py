import json

from django import get_version
from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

# 与 monitoring_snapshot 中 http_probes 键一致（供前端合并 HTTP 状态）
_HTTP_PROBE_KEY_BY_APP = {
    "aibroker": "aibroker_v1_health",
    "cdn": "cdn_health",
    "cms": "cms_health",
    "config": "config_health",
    "know": "know_health",
    "notice": "notice_health",
    "oss": "oss_health",
    "searchrec": "searchrec_health",
    "snowflake": "snowflake_health",
    "user": "user_health",
    "verify": "verify_health",
    "keepcon": "keepcon_health",
    "tcc": "tcc_health",
}

_APP_KEYS_ORDER = (
    "cdn",
    "know",
    "mail",
    "oss",
    "snowflake",
    "user",
    "notice",
    "verify",
    "aibroker",
    "searchrec",
    "cms",
    "config",
    "keepcon",
    "tcc",
)

_MANAGE_URL_NAME_BY_KEY = {
    "cdn": "console:cdn-distributions",
    "know": "console:know-batch-list",
    "mail": "console:mail-accounts",
    "oss": "console:oss-browser",
    "snowflake": "console:snowflake-callers",
    "user": "console:user-list",
    "notice": "console:notice-callers",
    "verify": "console:verify-callers",
    "aibroker": "console:aibroker-regs",
    "searchrec": "console:searchrec-console",
    "cms": "console:cms-dashboard",
    "config": "console:config-callers",
    "keepcon": "console:keepcon-devices",
    "tcc": "console:tcc-callers",
}


def _manage_href(key: str) -> str:
    name = _MANAGE_URL_NAME_BY_KEY.get(key)
    if not name:
        return ""
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


class DashboardView(TemplateView):
    template_name = "console/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["django_version"] = get_version()
        context["monitoring_refresh_ms"] = int(getattr(settings, "CONSOLE_MONITORING_REFRESH_MS", 0) or 0)
        context["http_probe_key_by_app"] = _HTTP_PROBE_KEY_BY_APP

        apps_raw = {
            "aibroker": {
                "name": "AI Broker",
                "enabled": getattr(settings, "APP_AIBROKER_ENABLED", False),
                "description": "统一 LLM 调用、提示词模版与调用方凭证",
                "icon": "sparkles",
            },
            "cdn": {
                "name": "CDN 分发",
                "enabled": getattr(settings, "APP_CDN_ENABLED", False),
                "description": "CloudFront 兼容的 CDN 分发与缓存失效管理",
                "icon": "globe",
            },
            "cms": {
                "name": "CMS",
                "enabled": getattr(settings, "APP_CMS_ENABLED", False),
                "description": "内容类型注册与内容行管理",
                "icon": "collection",
            },
            "config": {
                "name": "配置中心",
                "enabled": getattr(settings, "APP_CONFIG_ENABLED", False),
                "description": "条件化 KV 配置与调用方注册",
                "icon": "adjustments",
            },
            "keepcon": {
                "name": "长连接",
                "enabled": getattr(settings, "APP_KEEPCON_ENABLED", False),
                "description": "管理长连接",
                "icon": "connect",
            },
            "know": {
                "name": "知识管理",
                "enabled": getattr(settings, "APP_KNOW_ENABLED", False),
                "description": "管理知识条目、关系和摘要",
                "icon": "book",
            },
            "mail": {
                "name": "邮件服务",
                "enabled": getattr(settings, "APP_MAILSERVER_ENABLED", False),
                "description": "管理邮件账户和邮箱",
                "icon": "mail",
            },
            "notice": {
                "name": "通知中心",
                "enabled": getattr(settings, "APP_NOTICE_ENABLED", False),
                "description": "邮件/短信等通知发送与调用方管理",
                "icon": "bell",
            },
            "oss": {
                "name": "对象存储",
                "enabled": getattr(settings, "APP_OSS_ENABLED", False),
                "description": "S3 兼容的对象存储服务",
                "icon": "folder",
            },
            "searchrec": {
                "name": "搜索推荐",
                "enabled": getattr(settings, "APP_SEARCHREC_ENABLED", False),
                "description": "搜索、推荐、重排基础能力调试",
                "icon": "search",
            },
            "snowflake": {
                "name": "ID 生成",
                "enabled": getattr(settings, "APP_SNOWFLAKE_ENABLED", False),
                "description": "分布式 ID 生成服务",
                "icon": "hash",
            },
            "user": {
                "name": "用户中心",
                "enabled": getattr(settings, "APP_USER_ENABLED", False),
                "description": "统一用户注册、登录、资料和凭证管理",
                "icon": "user",
            },
            "verify": {
                "name": "校验中心",
                "enabled": getattr(settings, "APP_VERIFY_ENABLED", False),
                "description": "校验码生成、校验与调用方注册管理",
                "icon": "shield",
            },
            "tcc": {
                "name": "分布式事务",
                "enabled": getattr(settings, "APP_TCC_ENABLED", False),
                "description": "TCC 协调、参与者注册与事务扫描",
                "icon": "layers",
            },
        }

        apps_config = []
        for k in _APP_KEYS_ORDER:
            if k not in apps_raw:
                continue
            meta = apps_raw[k]
            apps_config.append(
                {
                    "key": k,
                    "name": meta["name"],
                    "enabled": meta["enabled"],
                    "description": meta["description"],
                    "icon": meta["icon"],
                    "href": _manage_href(k),
                    "httpProbeKey": _HTTP_PROBE_KEY_BY_APP.get(k)
                    or None,
                }
            )
        context["apps_config_json"] = json.dumps(apps_config, ensure_ascii=False)
        return context
