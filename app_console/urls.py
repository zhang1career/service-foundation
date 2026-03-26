from django.conf import settings
from django.urls import path

from app_console.views import (
    DashboardView,
    KnowListView,
    KnowPointDetailView,
    KnowPointEditView,
    KnowInsightView,
    KnowBatchListView,
    KnowBatchDetailView,
    KnowBatchEditView,
    MailAccountListView,
    MailboxListView,
    OssBrowserView,
    SnowflakeView,
    CdnDistributionListView,
    CdnDistributionDetailView,
    CdnDistributionEditView,
    UserListConsoleView,
    UserDetailConsoleView,
    UserEditConsoleView,
    UserEventListConsoleView,
    UserEventDetailConsoleView,
    UserEventEditConsoleView,
    NoticeRegConsoleView,
    VerifyRegConsoleView,
    SearchRecConsoleView,
)

app_name = 'console'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),

    # Knowledge management
    path('know/', KnowListView.as_view(), name='know-list'),
    path('know/batches/', KnowBatchListView.as_view(), name='know-batch-list'),
    path('know/batches/<int:entity_id>/', KnowBatchDetailView.as_view(), name='know-batch-detail'),
    path('know/batches/<int:entity_id>/edit/', KnowBatchEditView.as_view(), name='know-batch-edit'),
    path('know/points/<int:point_id>/', KnowPointDetailView.as_view(), name='know-point-detail'),
    path('know/points/<int:point_id>/edit/', KnowPointEditView.as_view(), name='know-point-edit'),
    path('know/insights/', KnowInsightView.as_view(), name='know-insights'),

    # Mail management
    path('mail/', MailAccountListView.as_view(), name='mail-accounts'),
    path('mail/<int:account_id>/mailboxes/', MailboxListView.as_view(), name='mail-mailboxes'),

    # OSS browser
    path('oss/', OssBrowserView.as_view(), name='oss-browser'),

    # Snowflake ID generator
    path('snowflake/', SnowflakeView.as_view(), name='snowflake'),

    # CDN management
    path('cdn/', CdnDistributionListView.as_view(), name='cdn-distributions'),
    path(
        'cdn/distributions/<str:distribution_id>/edit/',
        CdnDistributionEditView.as_view(),
        name='cdn-distribution-edit',
    ),
    path('cdn/distributions/<str:distribution_id>/', CdnDistributionDetailView.as_view(), name='cdn-distribution-detail'),
    path('user/', UserListConsoleView.as_view(), name='user-list'),
    path('user/events/', UserEventListConsoleView.as_view(), name='user-event-list'),
    path('user/events/<int:event_id>/', UserEventDetailConsoleView.as_view(), name='user-event-detail'),
    path('user/events/<int:event_id>/edit/', UserEventEditConsoleView.as_view(), name='user-event-edit'),
    path('user/<int:user_id>/', UserDetailConsoleView.as_view(), name='user-detail'),
    path('user/<int:user_id>/edit/', UserEditConsoleView.as_view(), name='user-edit'),
    path('notice/regs/', NoticeRegConsoleView.as_view(), name='notice-reg-list'),
    path('verify/regs/', VerifyRegConsoleView.as_view(), name='verify-reg-list'),
    path('searchrec/', SearchRecConsoleView.as_view(), name='searchrec-console'),
]

if getattr(settings, "APP_AIBROKER_ENABLED", False):
    from app_console.views.aibroker_view import (
        AibrokerModelConsoleView,
        AibrokerPromptTemplateConsoleView,
        AibrokerProviderConsoleView,
        AibrokerRegConsoleView,
    )

    urlpatterns.extend(
        [
            path("aibroker/", AibrokerRegConsoleView.as_view(), name="aibroker-regs"),
            path("aibroker/providers/", AibrokerProviderConsoleView.as_view(), name="aibroker-providers"),
            path(
                "aibroker/providers/<int:provider_id>/models/",
                AibrokerModelConsoleView.as_view(),
                name="aibroker-models",
            ),
            path(
                "aibroker/templates/",
                AibrokerPromptTemplateConsoleView.as_view(),
                name="aibroker-prompt-templates",
            ),
        ]
    )
