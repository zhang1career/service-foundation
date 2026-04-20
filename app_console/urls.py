from django.conf import settings
from django.urls import path, re_path

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
    SnowflakeCallerListView,
    SnowflakeGenerateView,
    SnowflakeHistoryView,
    SnowflakeParseView,
    CdnDistributionListView,
    CdnDistributionDetailView,
    CdnDistributionEditView,
    UserListConsoleView,
    UserDetailConsoleView,
    UserEditConsoleView,
    UserEventListConsoleView,
    UserEventDetailConsoleView,
    UserEventEditConsoleView,
    NoticeDetailConsoleView,
    NoticeListConsoleView,
    NoticeManualSendConsoleView,
    NoticeRegConsoleView,
    SearchRecConsoleView,
    SearchRecRegConsoleView,
    VerifyCallerConsoleView,
    VerifyCodeDetailConsoleView,
    VerifyCodeListConsoleView,
    VerifyLogDetailConsoleView,
    VerifyLogListConsoleView,
)
from app_console.views.auth_view import ConsoleLoginView, ConsoleLogoutView
from app_console.views.monitoring_api_view import MonitoringJsonView, MonitoringSnapshotView

app_name = 'console'

urlpatterns = [
    path("login/", ConsoleLoginView.as_view(), name="login"),
    path("logout/", ConsoleLogoutView.as_view(), name="logout"),
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),
    path("api/monitoring/snapshot/", MonitoringSnapshotView.as_view(), name="monitoring-snapshot"),
    path("api/monitoring.json", MonitoringJsonView.as_view(), name="monitoring-json"),

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
    path('snowflake/callers/', SnowflakeCallerListView.as_view(), name='snowflake-callers'),
    path('snowflake/generate/', SnowflakeGenerateView.as_view(), name='snowflake-generate'),
    path('snowflake/parse/', SnowflakeParseView.as_view(), name='snowflake-parse'),
    path('snowflake/history/', SnowflakeHistoryView.as_view(), name='snowflake-history'),

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
    path('notice/notices/', NoticeListConsoleView.as_view(), name='notice-notices'),
    path('notice/notices/<int:notice_id>/', NoticeDetailConsoleView.as_view(), name='notice-record-detail'),
    path('notice/callers/', NoticeRegConsoleView.as_view(), name='notice-callers'),
    path('notice/invoke/', NoticeManualSendConsoleView.as_view(), name='notice-invoke'),
    path('verify/callers/', VerifyCallerConsoleView.as_view(), name='verify-callers'),
    path('verify/codes/', VerifyCodeListConsoleView.as_view(), name='verify-code-list'),
    path('verify/codes/<int:code_id>/', VerifyCodeDetailConsoleView.as_view(), name='verify-code-detail'),
    path('verify/history/', VerifyLogListConsoleView.as_view(), name='verify-history-list'),
    path('verify/history/<int:log_id>/', VerifyLogDetailConsoleView.as_view(), name='verify-history-detail'),
    path('searchrec/', SearchRecRegConsoleView.as_view(), name='searchrec-console'),
    path('searchrec/api/', SearchRecConsoleView.as_view(), name='searchrec-api'),
]

if getattr(settings, 'APP_CMS_ENABLED', False):
    from app_console.views.cms_view import (
        CmsContentItemCreateView,
        CmsContentItemDeleteView,
        CmsContentItemEditView,
        CmsContentItemListView,
        CmsContentMetaCreateView,
        CmsContentMetaDeleteView,
        CmsContentMetaEditView,
        CmsContentMetaIndexView,
        CmsDashboardView,
    )

    urlpatterns.extend(
        [
            path('cms/', CmsDashboardView.as_view(), name='cms-dashboard'),
            path('cms/content-meta/create/', CmsContentMetaCreateView.as_view(), name='cms-content-meta-create'),
            path(
                'cms/content-meta/<int:pk>/delete/',
                CmsContentMetaDeleteView.as_view(),
                name='cms-content-meta-delete',
            ),
            path('cms/content-meta/<int:pk>/edit/', CmsContentMetaEditView.as_view(), name='cms-content-meta-edit'),
            path('cms/content-meta/', CmsContentMetaIndexView.as_view(), name='cms-content-meta-index'),
            re_path(
                r'^cms/content/(?P<content_route>[a-z0-9][a-z0-9_-]*)/create/$',
                CmsContentItemCreateView.as_view(),
                name='cms-content-create',
            ),
            re_path(
                r'^cms/content/(?P<content_route>[a-z0-9][a-z0-9_-]*)/(?P<record_id>[0-9]+)/delete/$',
                CmsContentItemDeleteView.as_view(),
                name='cms-content-delete',
            ),
            re_path(
                r'^cms/content/(?P<content_route>[a-z0-9][a-z0-9_-]*)/(?P<record_id>[0-9]+)/edit/$',
                CmsContentItemEditView.as_view(),
                name='cms-content-edit',
            ),
            re_path(
                r'^cms/content/(?P<content_route>[a-z0-9][a-z0-9_-]*)/$',
                CmsContentItemListView.as_view(),
                name='cms-content-index',
            ),
        ]
    )

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

if getattr(settings, "APP_CONFIG_ENABLED", False):
    from app_console.views.config_console_view import (
        ConfigConditionFieldsConsoleView,
        ConfigEntriesConsoleView,
        ConfigRegConsoleView,
    )

    urlpatterns.extend(
        [
            path("config/callers/", ConfigRegConsoleView.as_view(), name="config-callers"),
            path("config/entries/", ConfigEntriesConsoleView.as_view(), name="config-entries"),
            path(
                "config/condition-fields/",
                ConfigConditionFieldsConsoleView.as_view(),
                name="config-condition-fields",
            ),
        ]
    )

if getattr(settings, "APP_KEEPCON_ENABLED", False):
    from app_console.views.keepcon_console_view import (
        KeepconDevicesConsoleView,
        KeepconMessagesConsoleView,
        KeepconRegConsoleView,
    )

    urlpatterns.extend(
        [
            path("keepcon/callers/", KeepconRegConsoleView.as_view(), name="keepcon-callers"),
            path("keepcon/devices/", KeepconDevicesConsoleView.as_view(), name="keepcon-devices"),
            path("keepcon/messages/", KeepconMessagesConsoleView.as_view(), name="keepcon-messages"),
        ]
    )

if getattr(settings, "APP_TCC_ENABLED", False):
    from app_console.views.tcc_console_view import (
        TccBizListConsoleView,
        TccBranchMetaConsoleView,
        TccManualConsoleView,
        TccParticipantConsoleView,
        TccTxDetailConsoleView,
        TccTxListConsoleView,
    )

    urlpatterns.extend(
        [
            path("tcc/callers/", TccParticipantConsoleView.as_view(), name="tcc-callers"),
            path("tcc/businesses/", TccBizListConsoleView.as_view(), name="tcc-businesses"),
            path(
                "tcc/biz/<int:biz_id>/branches/",
                TccBranchMetaConsoleView.as_view(),
                name="tcc-branch-meta",
            ),
            path("tcc/transactions/", TccTxListConsoleView.as_view(), name="tcc-transactions"),
            path(
                "tcc/transactions/<int:tx_id>/",
                TccTxDetailConsoleView.as_view(),
                name="tcc-transaction-detail",
            ),
            path("tcc/manual/", TccManualConsoleView.as_view(), name="tcc-manual"),
        ]
    )

if getattr(settings, "APP_SAGA_ENABLED", False):
    from app_console.views.saga_console_view import (
        SagaFlowListConsoleView,
        SagaFlowStepsConsoleView,
        SagaInstanceDetailConsoleView,
        SagaInstanceListConsoleView,
        SagaParticipantConsoleView,
    )

    urlpatterns.extend(
        [
            path("saga/callers/", SagaParticipantConsoleView.as_view(), name="saga-callers"),
            path("saga/flows/", SagaFlowListConsoleView.as_view(), name="saga-flows"),
            path(
                "saga/flows/<int:flow_id>/steps/",
                SagaFlowStepsConsoleView.as_view(),
                name="saga-flow-steps",
            ),
            path("saga/instances/", SagaInstanceListConsoleView.as_view(), name="saga-instances"),
            path(
                "saga/instances/<int:instance_id>/",
                SagaInstanceDetailConsoleView.as_view(),
                name="saga-instance-detail",
            ),
        ]
    )
