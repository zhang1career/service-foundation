"""
Console catalog: sidebar / dashboard app metadata and reverse URL names.

``local_enabled`` reflects this process's APP_* flags (see ``local_setting_attr``).
Listing apps in the UI does not depend on those flags — only badges and optional DB rows do.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings as django_settings
from django.urls import NoReverseMatch, reverse

APP_KEYS_ORDER: tuple[str, ...] = (
    "cdn",
    "know",
    "mail",
    "oss",
    "snowflake",
    "user",
    "notice",
    "verify",
    "textmod",
    "aibroker",
    "searchrec",
    "cms",
    "config",
    "keepcon",
    "tcc",
    "saga",
)

HTTP_PROBE_KEY_BY_APP: dict[str, str] = {
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
    "textmod": "textmod_health",
    "keepcon": "keepcon_health",
    "tcc": "tcc_health",
    "saga": "saga_health",
}

_MANAGE_URL_NAME_BY_KEY: dict[str, str] = {
    "cdn": "console:cdn-distributions",
    "know": "console:know-batch-list",
    "mail": "console:mail-accounts",
    "oss": "console:oss-browser",
    "snowflake": "console:snowflake-callers",
    "user": "console:user-list",
    "notice": "console:notice-callers",
    "verify": "console:verify-callers",
    "textmod": "console:textmod-lexicons",
    "aibroker": "console:aibroker-regs",
    "searchrec": "console:searchrec-console",
    "cms": "console:cms-dashboard",
    "config": "console:config-callers",
    "keepcon": "console:keepcon-devices",
    "tcc": "console:tcc-callers",
    "saga": "console:saga-callers",
}

_APP_ENTRIES: dict[str, dict[str, str]] = {
    "know": {
        "name": "知识管理",
        "description": "管理知识条目、关系和摘要",
        "icon": "book",
        "local_setting": "APP_KNOW_ENABLED",
    },
    "mail": {
        "name": "邮件服务",
        "description": "管理邮件账户和邮箱",
        "icon": "mail",
        "local_setting": "APP_MAILSERVER_ENABLED",
    },
    "oss": {
        "name": "对象存储",
        "description": "S3 兼容的对象存储服务",
        "icon": "folder",
        "local_setting": "APP_OSS_ENABLED",
    },
    "snowflake": {
        "name": "ID 生成",
        "description": "分布式 ID 生成服务",
        "icon": "hash",
        "local_setting": "APP_SNOWFLAKE_ENABLED",
    },
    "cdn": {
        "name": "CDN 分发",
        "description": "CloudFront 兼容的 CDN 分发与缓存失效管理",
        "icon": "globe",
        "local_setting": "APP_CDN_ENABLED",
    },
    "user": {
        "name": "用户中心",
        "description": "统一用户注册、登录、资料和凭证管理",
        "icon": "user",
        "local_setting": "APP_USER_ENABLED",
    },
    "verify": {
        "name": "校验中心",
        "description": "校验码生成、校验与调用方注册管理",
        "icon": "shield",
        "local_setting": "APP_VERIFY_ENABLED",
    },
    "textmod": {
        "name": "文本风控",
        "description": "本地词库、归一化与关键词扫描快照",
        "icon": "document-text",
        "local_setting": "APP_TEXTMOD_ENABLED",
    },
    "notice": {
        "name": "通知中心",
        "description": "邮件/短信等通知发送与调用方管理",
        "icon": "bell",
        "local_setting": "APP_NOTICE_ENABLED",
    },
    "aibroker": {
        "name": "AI Broker",
        "description": "统一 LLM 调用、提示词模版与调用方凭证",
        "icon": "sparkles",
        "local_setting": "APP_AIBROKER_ENABLED",
    },
    "searchrec": {
        "name": "搜索推荐",
        "description": "搜索、推荐、重排基础能力调试",
        "icon": "search",
        "local_setting": "APP_SEARCHREC_ENABLED",
    },
    "cms": {
        "name": "CMS",
        "description": "内容类型注册与内容行管理",
        "icon": "collection",
        "local_setting": "APP_CMS_ENABLED",
    },
    "config": {
        "name": "配置中心",
        "description": "条件化 KV 配置与调用方注册",
        "icon": "adjustments",
        "local_setting": "APP_CONFIG_ENABLED",
    },
    "keepcon": {
        "name": "长连接",
        "description": "WebSocket 推送与设备消息",
        "icon": "connect",
        "local_setting": "APP_KEEPCON_ENABLED",
    },
    "tcc": {
        "name": "TCC",
        "description": "TCC 协调、参与者注册与事务扫描",
        "icon": "layers",
        "local_setting": "APP_TCC_ENABLED",
    },
    "saga": {
        "name": "SAGA",
        "description": "线性 Saga 流程编排与实例",
        "icon": "bolt",
        "local_setting": "APP_SAGA_ENABLED",
    },
}


def manage_href(key: str) -> str:
    name = _MANAGE_URL_NAME_BY_KEY.get(key)
    if not name:
        return ""
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def local_enabled(key: str, settings_obj: Any = None) -> bool:
    """Whether this Django process has the app module enabled (APP_* flag)."""
    meta = _APP_ENTRIES.get(key)
    if not meta:
        return False
    so = settings_obj if settings_obj is not None else django_settings
    return bool(getattr(so, meta["local_setting"], False))


def build_apps_for_console_context(settings_obj: Any) -> dict[str, dict[str, Any]]:
    """Sidebar / template context: metadata, local flag, and resolved console URL if any."""
    out: dict[str, dict[str, Any]] = {}
    for key, meta in _APP_ENTRIES.items():
        out[key] = {
            "name": meta["name"],
            "description": meta["description"],
            "icon": meta["icon"],
            "local_enabled": local_enabled(key, settings_obj),
            "console_href": manage_href(key),
        }
    return out


def build_apps_config_list(settings_obj: Any) -> list[dict[str, Any]]:
    """Dashboard monitoring cards (serialized to JSON for the browser)."""
    apps_config: list[dict[str, Any]] = []
    for key in APP_KEYS_ORDER:
        meta = _APP_ENTRIES[key]
        apps_config.append(
            {
                "key": key,
                "name": meta["name"],
                "local_enabled": local_enabled(key, settings_obj),
                "description": meta["description"],
                "icon": meta["icon"],
                "href": manage_href(key),
                "httpProbeKey": HTTP_PROBE_KEY_BY_APP.get(key) or None,
            }
        )
    return apps_config
