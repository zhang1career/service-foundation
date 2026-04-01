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
    SearchRecConsoleView,
    VerifyCallerConsoleView,
    VerifyCodeDetailConsoleView,
    VerifyCodeListConsoleView,
    VerifyLogDetailConsoleView,
    VerifyLogListConsoleView,
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
    path('verify/callers/', VerifyCallerConsoleView.as_view(), name='verify-callers'),
    path('verify/codes/', VerifyCodeListConsoleView.as_view(), name='verify-code-list'),
    path('verify/codes/<int:code_id>/', VerifyCodeDetailConsoleView.as_view(), name='verify-code-detail'),
    path('verify/history/', VerifyLogListConsoleView.as_view(), name='verify-history-list'),
    path('verify/history/<int:log_id>/', VerifyLogDetailConsoleView.as_view(), name='verify-history-detail'),
    path('searchrec/', SearchRecConsoleView.as_view(), name='searchrec-console'),
]

if getattr(settings, "APP_AIBROKER_ENABLED", False):
    from app_console.views.aibroker_view import (
        AibrokerCallLogConsoleView,
        AibrokerCallLogDetailConsoleView,
        AibrokerDebugConsoleView,
        AibrokerDebugInvokeView,
        AibrokerDebugVideoResultView,
        AibrokerDebugUploadImageView,
        AibrokerModelConsoleView,
        AibrokerModelDetailConsoleView,
        AibrokerPromptTemplateConsoleView,
        AibrokerPromptTemplateDetailConsoleView,
        AibrokerProviderConsoleView,
        AibrokerProviderDetailConsoleView,
        AibrokerRegConsoleView,
    )

    urlpatterns.extend(
        [
            path("aibroker/", AibrokerRegConsoleView.as_view(), name="aibroker-regs"),
            path("aibroker/providers/", AibrokerProviderConsoleView.as_view(), name="aibroker-providers"),
            path(
                "aibroker/providers/<int:provider_id>/",
                AibrokerProviderDetailConsoleView.as_view(),
                name="aibroker-provider-detail",
            ),
            path(
                "aibroker/providers/<int:provider_id>/models/",
                AibrokerModelConsoleView.as_view(),
                name="aibroker-models",
            ),
            path(
                "aibroker/providers/<int:provider_id>/models/<int:model_id>/",
                AibrokerModelDetailConsoleView.as_view(),
                name="aibroker-model-detail",
            ),
            path(
                "aibroker/templates/<int:template_id>/",
                AibrokerPromptTemplateDetailConsoleView.as_view(),
                name="aibroker-prompt-template-detail",
            ),
            path(
                "aibroker/templates/",
                AibrokerPromptTemplateConsoleView.as_view(),
                name="aibroker-prompt-templates",
            ),
            path("aibroker/debug/invoke/", AibrokerDebugInvokeView.as_view(), name="aibroker-debug-invoke"),
            path("aibroker/debug/video-result/", AibrokerDebugVideoResultView.as_view(), name="aibroker-debug-video-result"),
            path("aibroker/debug/upload-image/", AibrokerDebugUploadImageView.as_view(), name="aibroker-debug-upload-image"),
            path("aibroker/debug/", AibrokerDebugConsoleView.as_view(), name="aibroker-debug"),
            path(
                "aibroker/call-logs/<int:log_id>/",
                AibrokerCallLogDetailConsoleView.as_view(),
                name="aibroker-call-log-detail",
            ),
            path("aibroker/call-logs/", AibrokerCallLogConsoleView.as_view(), name="aibroker-call-logs"),
        ]
    )
