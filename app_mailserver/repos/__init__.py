"""
Mail server repositories

This module exports all repository functions for database operations.
"""
from app_mailserver.repos.mail_account_repo import (
    get_account_by_id,
    get_account_by_username,
    get_account_by_username_any,
    list_accounts,
    create_account,
    update_account,
    delete_account,
)
from app_mailserver.repos.mailbox_repo import (
    get_mailbox_by_account_and_path,
    get_mailboxes_by_account,
    get_or_create_mailbox,
    get_mailbox_by_id,
    create_mailbox,
    update_mailbox,
    delete_mailbox,
)
from app_mailserver.repos.mail_message_repo import (
    create_mail_message,
    get_mail_message_by_id,
    get_messages_by_mailbox,
    count_messages_by_mailbox,
    count_unread_messages_by_mailbox,
    update_message_read_status,
    delete_mail_message,
)
from app_mailserver.repos.mail_attachment_repo import (
    create_mail_attachment,
    get_attachment_by_id,
    get_attachments_by_message,
    delete_attachments_by_message,
)

__all__ = [
    # Mail account
    'get_account_by_id',
    'get_account_by_username',
    'get_account_by_username_any',
    'list_accounts',
    'create_account',
    'update_account',
    'delete_account',
    # Mailbox
    'get_mailbox_by_account_and_path',
    'get_mailboxes_by_account',
    'get_or_create_mailbox',
    'get_mailbox_by_id',
    'create_mailbox',
    'update_mailbox',
    'delete_mailbox',
    # Mail message
    'create_mail_message',
    'get_mail_message_by_id',
    'get_messages_by_mailbox',
    'count_messages_by_mailbox',
    'count_unread_messages_by_mailbox',
    'update_message_read_status',
    'delete_mail_message',
    # Mail attachment
    'create_mail_attachment',
    'get_attachment_by_id',
    'get_attachments_by_message',
    'delete_attachments_by_message',
]

