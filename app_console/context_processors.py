import time

from django.conf import settings

from common.utils.django_util import setting_str

from app_console.catalog import build_apps_for_console_context

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
        'console_snowflake_access_key': setting_str('CONSOLE_SNOWFLAKE_ACCESS_KEY', ''),
        'apps': build_apps_for_console_context(settings),
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
