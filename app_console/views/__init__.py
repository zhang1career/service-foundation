from .dashboard_view import DashboardView
from .know_view import (
    KnowListView,
    KnowPointDetailView,
    KnowPointEditView,
    KnowInsightView,
    KnowBatchListView,
    KnowBatchDetailView,
    KnowBatchEditView,
)
from .mail_view import MailAccountListView, MailboxListView
from .oss_view import OssBrowserView
from .snowflake_view import SnowflakeView
from .cdn_view import (
    CdnDistributionListView,
    CdnDistributionDetailView,
    CdnDistributionEditView,
)

__all__ = [
    'DashboardView',
    'KnowListView',
    'KnowPointDetailView',
    'KnowPointEditView',
    'KnowInsightView',
    'KnowBatchListView',
    'KnowBatchDetailView',
    'KnowBatchEditView',
    'MailAccountListView',
    'MailboxListView',
    'OssBrowserView',
    'SnowflakeView',
    'CdnDistributionListView',
    'CdnDistributionDetailView',
    'CdnDistributionEditView',
]
