from django.urls import path

from app_mailserver.views.mail_account_view import (
    MailAccountListView,
    MailAccountDetailView,
)
from app_mailserver.views.mailbox_view import (
    MailboxListView,
    MailboxDetailView,
)

# URL patterns for mail server REST API
# SMTP/IMAP protocols are handled separately via start_mail_server command
# These REST API endpoints are for mail account and mailbox management

urlpatterns = [
    # Mail account CRUD endpoints
    path('accounts', MailAccountListView.as_view(), name='mail-account-list'),
    path('accounts/<int:account_id>', MailAccountDetailView.as_view(), name='mail-account-detail'),
    # Mailbox CRUD endpoints
    path('accounts/<int:account_id>/mailboxes', MailboxListView.as_view(), name='mailbox-list'),
    path('mailboxes/<int:mailbox_id>', MailboxDetailView.as_view(), name='mailbox-detail'),
]

