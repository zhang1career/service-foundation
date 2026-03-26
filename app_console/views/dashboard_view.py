from django.conf import settings
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = 'console/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['apps'] = {
            'cdn': {
                'name': 'CDN 分发',
                'enabled': getattr(settings, 'APP_CDN_ENABLED', False),
                'description': 'CloudFront 兼容的 CDN 分发与缓存失效管理',
                'icon': 'globe',
            },
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
            'user': {
                'name': '用户中心',
                'enabled': getattr(settings, 'APP_USER_ENABLED', False),
                'description': '统一用户注册、登录、资料和凭证管理',
                'icon': 'user',
            },
            'notice': {
                'name': '通知中心',
                'enabled': getattr(settings, 'APP_NOTICE_ENABLED', False),
                'description': '邮件/短信等通知发送与调用方管理',
                'icon': 'bell',
            },
            'verify': {
                'name': '校验工具',
                'enabled': getattr(settings, 'APP_VERIFY_ENABLED', False),
                'description': '验证码生成、校验与调用方注册管理',
                'icon': 'shield',
            },
            'aibroker': {
                'name': 'AI Broker',
                'enabled': getattr(settings, 'APP_AIBROKER_ENABLED', False),
                'description': '统一 LLM 调用、提示模板与调用方凭证',
                'icon': 'sparkles',
            },
            'searchrec': {
                'name': '搜索推荐',
                'enabled': getattr(settings, 'APP_SEARCHREC_ENABLED', False),
                'description': '搜索、推荐、重排基础能力调试',
                'icon': 'search',
            },
        }
        return context
