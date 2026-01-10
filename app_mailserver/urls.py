from django.urls import path

from app_mailserver.views.mail_account_view import (
    MailAccountListView,
    MailAccountDetailView,
)

# URL patterns for mail server REST API
# SMTP/IMAP protocols are handled separately via start_mail_server command
# These REST API endpoints are for mail account management

urlpatterns = [
    # Mail account CRUD endpoints
    path('accounts', MailAccountListView.as_view(), name='mail-account-list'),
    path('accounts/<int:account_id>', MailAccountDetailView.as_view(), name='mail-account-detail'),
]

