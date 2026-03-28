"""service_foundation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
]

# Add console URL if enabled
if settings.APP_CONSOLE_ENABLED:
    from app_console import urls as app_console_urls
    urlpatterns.append(path('console/', include(app_console_urls)))

# Dynamically add URL patterns based on enabled apps
if settings.APP_AIBROKER_ENABLED:
    from app_aibroker import urls as app_aibroker_urls

    urlpatterns.append(path("api/ai/", include(app_aibroker_urls)))

if settings.APP_CDN_ENABLED:
    from common.views.dict_codes_view import DictCodesView
    from app_cdn import urls as app_cdn_urls
    urlpatterns.append(path("api/cdn/dict", DictCodesView.as_view(), name="cdn-dict"))
    urlpatterns.append(path("api/cdn/2020-05-31/", include(app_cdn_urls)))

if settings.APP_KNOW_ENABLED:
    from app_know import urls as app_know_urls
    urlpatterns.append(path('api/know/', include(app_know_urls)))

if settings.APP_MAILSERVER_ENABLED:
    from app_mailserver import urls as app_mailserver_urls
    urlpatterns.append(path('api/mail/', include(app_mailserver_urls)))

if settings.APP_NOTICE_ENABLED:
    from app_notice import urls as app_notice_urls
    urlpatterns.append(path('api/notice/', include(app_notice_urls)))

if settings.APP_OSS_ENABLED:
    from app_oss import urls as app_oss_urls
    urlpatterns.append(path('api/oss/', include(app_oss_urls)))

if settings.APP_SEARCHREC_ENABLED:
    from app_searchrec import urls as app_searchrec_urls
    urlpatterns.append(path('api/searchrec/', include(app_searchrec_urls)))

if settings.APP_SNOWFLAKE_ENABLED:
    from app_snowflake import urls as app_snowflake_urls
    urlpatterns.append(path('api/snowflake/', include(app_snowflake_urls)))

if settings.APP_USER_ENABLED:
    from app_user import urls as app_user_urls
    urlpatterns.append(path('api/user/', include(app_user_urls)))

if settings.APP_VERIFY_ENABLED:
    from app_verify import urls as app_verify_urls
    urlpatterns.append(path('api/verify/', include(app_verify_urls)))
