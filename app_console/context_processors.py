from django.conf import settings


def console_context(request):
    """Provide app status to all console templates."""
    return {
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
        }
    }
