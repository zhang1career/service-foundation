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
if settings.APP_MAILSERVER_ENABLED:
    from app_mailserver import urls as app_mailserver_urls
    urlpatterns.append(path('api/mail/', include(app_mailserver_urls)))

if settings.APP_OSS_ENABLED:
    from app_oss import urls as app_oss_urls
    urlpatterns.append(path('api/oss/', include(app_oss_urls)))

if settings.APP_SNOWFLAKE_ENABLED:
    from app_snowflake import urls as app_snowflake_urls
    urlpatterns.append(path('api/snowflake/', include(app_snowflake_urls)))

if settings.APP_KNOW_ENABLED:
    from app_know import urls as app_know_urls
    urlpatterns.append(path('api/know/', include(app_know_urls)))
