from django.urls import path

from app_console.views import (
    DashboardView,
    KnowListView,
    KnowDetailView,
    KnowRelationshipView,
    KnowSummaryView,
    KnowPerspectiveView,
    KnowInsightView,
    KnowBatchListView,
    KnowBatchDetailView,
    KnowBatchEditView,
    MailAccountListView,
    MailboxListView,
    OssBrowserView,
    SnowflakeView,
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
    path('know/<int:entity_id>/', KnowDetailView.as_view(), name='know-detail'),
    path('know/relationships/', KnowRelationshipView.as_view(), name='know-relationships'),
    path('know/summaries/', KnowSummaryView.as_view(), name='know-summaries'),
    path('know/perspectives/', KnowPerspectiveView.as_view(), name='know-perspectives'),
    path('know/insights/', KnowInsightView.as_view(), name='know-insights'),

    # Mail management
    path('mail/', MailAccountListView.as_view(), name='mail-accounts'),
    path('mail/<int:account_id>/mailboxes/', MailboxListView.as_view(), name='mail-mailboxes'),

    # OSS browser
    path('oss/', OssBrowserView.as_view(), name='oss-browser'),

    # Snowflake ID generator
    path('snowflake/', SnowflakeView.as_view(), name='snowflake'),
]
