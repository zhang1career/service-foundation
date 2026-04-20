import time

from django.conf import settings

# 进程内唯一静态版本号（首次请求时确定，用于缓存破坏）
_static_version = None


def _get_static_version():
    global _static_version
    if _static_version is None:
        _static_version = int(time.time())
    return _static_version


def console_context(request):
    """Provide app status and static cache-bust version to all console templates."""
    return {
        'static_version': _get_static_version(),
        'console_snowflake_access_key': getattr(settings, 'CONSOLE_SNOWFLAKE_ACCESS_KEY', '') or '',
        'apps': {
            'know': {
                'name': '知识管理',
                'enabled': getattr(settings, 'APP_KNOW_ENABLED', False),
                'description': '管理知识条目、关系和摘要',
                'icon': 'book',
            },
            'mail': {
                'name': '邮件服务',
                'enabled': getattr(settings, 'APP_MAILSERVER_ENABLED', False),
                'description': '管理邮件账户和邮箱',
                'icon': 'mail',
            },
            'oss': {
                'name': '对象存储',
                'enabled': getattr(settings, 'APP_OSS_ENABLED', False),
                'description': 'S3 兼容的对象存储服务',
                'icon': 'folder',
            },
            'snowflake': {
                'name': 'ID 生成',
                'enabled': getattr(settings, 'APP_SNOWFLAKE_ENABLED', False),
                'description': '分布式 ID 生成服务',
                'icon': 'hash',
            },
            'cdn': {
                'name': 'CDN 分发',
                'enabled': getattr(settings, 'APP_CDN_ENABLED', False),
                'description': 'CloudFront 兼容的 CDN 分发与缓存失效管理',
                'icon': 'globe',
            },
            'user': {
                'name': '用户中心',
                'enabled': getattr(settings, 'APP_USER_ENABLED', False),
                'description': '统一用户注册、登录、资料和凭证管理',
                'icon': 'user',
            },
            'verify': {
                'name': '校验中心',
                'enabled': getattr(settings, 'APP_VERIFY_ENABLED', False),
                'description': '校验码生成、校验与调用方注册管理',
                'icon': 'shield',
            },
            'notice': {
                'name': '通知中心',
                'enabled': getattr(settings, 'APP_NOTICE_ENABLED', False),
                'description': '邮件/短信等通知发送与调用方管理',
                'icon': 'bell',
            },
            'aibroker': {
                'name': 'AI Broker',
                'enabled': getattr(settings, 'APP_AIBROKER_ENABLED', False),
                'description': '统一 LLM 调用、提示词模版与调用方凭证',
                'icon': 'sparkles',
            },
            'searchrec': {
                'name': '搜索推荐',
                'enabled': getattr(settings, 'APP_SEARCHREC_ENABLED', False),
                'description': '搜索、推荐、重排基础能力调试',
                'icon': 'search',
            },
            'cms': {
                'name': 'CMS',
                'enabled': getattr(settings, 'APP_CMS_ENABLED', False),
                'description': '内容类型注册与内容行管理',
                'icon': 'collection',
            },
            'config': {
                'name': '配置中心',
                'enabled': getattr(settings, 'APP_CONFIG_ENABLED', False),
                'description': '条件化 KV 配置与调用方注册',
                'icon': 'adjustments',
            },
            'keepcon': {
                'name': '长连接',
                'enabled': getattr(settings, 'APP_KEEPCON_ENABLED', False),
                'description': 'WebSocket 推送与设备消息',
                'icon': 'link',
            },
            'tcc': {
                'name': 'TCC',
                'enabled': getattr(settings, 'APP_TCC_ENABLED', False),
                'description': 'TCC 协调、参与者注册与事务扫描',
                'icon': 'layers',
            },
            'saga': {
                'name': 'SAGA',
                'enabled': getattr(settings, 'APP_SAGA_ENABLED', False),
                'description': '线性 Saga 流程编排与实例',
                'icon': 'layers',
            },
        },
        'cms_content_metas': _cms_content_metas_for_sidebar(),
    }


def _cms_content_metas_for_sidebar():
    if not getattr(settings, "APP_CMS_ENABLED", False):
        return []
    try:
        from app_cms.models.content_meta import CmsContentMeta

        return list(CmsContentMeta.objects.order_by("name"))
    except Exception:
        return []
