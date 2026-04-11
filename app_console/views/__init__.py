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
from .snowflake_console_view import (
    SnowflakeCallerListView,
    SnowflakeGenerateView,
    SnowflakeHistoryView,
    SnowflakeParseView,
)
from .cdn_view import (
    CdnDistributionListView,
    CdnDistributionDetailView,
    CdnDistributionEditView,
)
from .user_view import UserListConsoleView, UserDetailConsoleView, UserEditConsoleView
from .event_view import UserEventListConsoleView, UserEventDetailConsoleView, UserEventEditConsoleView
from .notice_console_view import NoticeDetailConsoleView, NoticeListConsoleView
from .notice_manual_send_view import NoticeManualSendConsoleView
from .reg_console_view import NoticeRegConsoleView, VerifyRegConsoleView
from .searchrec_view import SearchRecConsoleView, SearchRecRegConsoleView
from .verify_console_view import (
    VerifyCallerConsoleView,
    VerifyCodeDetailConsoleView,
    VerifyCodeListConsoleView,
    VerifyLogDetailConsoleView,
    VerifyLogListConsoleView,
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
    'SnowflakeCallerListView',
    'SnowflakeGenerateView',
    'SnowflakeHistoryView',
    'SnowflakeParseView',
    'CdnDistributionListView',
    'CdnDistributionDetailView',
    'CdnDistributionEditView',
    'UserListConsoleView',
    'UserDetailConsoleView',
    'UserEditConsoleView',
    'UserEventListConsoleView',
    'UserEventDetailConsoleView',
    'UserEventEditConsoleView',
    'NoticeDetailConsoleView',
    'NoticeListConsoleView',
    'NoticeManualSendConsoleView',
    'NoticeRegConsoleView',
    'VerifyCallerConsoleView',
    'VerifyCodeDetailConsoleView',
    'VerifyCodeListConsoleView',
    'VerifyLogDetailConsoleView',
    'VerifyLogListConsoleView',
    'VerifyRegConsoleView',
    'SearchRecConsoleView',
    'SearchRecRegConsoleView',
]
