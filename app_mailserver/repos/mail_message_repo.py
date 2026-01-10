"""
Mail message repository

This module provides database operations for MailMessage model.
"""
import logging
from typing import Optional, List

from app_mailserver.models.mail_message import MailMessage
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)


def create_mail_message(
        account_id: int,
        mailbox_id: int,
        message_id: str,
        subject: str,
        from_address: str,
        to_addresses: str = '',
        cc_addresses: str = '',
        bcc_addresses: str = '',
        text_body: str = '',
        html_body: str = '',
        mt: int = 0,
        size: int = 0,
        raw_message: str = '',
        ct: int = 0,
        dt: int = 0,
        is_read: bool = False,
        is_flagged: bool = False
) -> MailMessage:
    """
    Create a new mail message
    
    Args:
        account_id: Account ID
        mailbox_id: Mailbox ID
        message_id: Message-ID header
        subject: Email subject
        from_address: From address
        to_addresses: To addresses (comma-separated)
        cc_addresses: CC addresses (comma-separated)
        bcc_addresses: BCC addresses (comma-separated)
        text_body: Plain text body
        html_body: HTML body
        mt: Message timestamp (milliseconds)
        size: Message size in bytes
        raw_message: Raw email message
        ct: Create timestamp (milliseconds)
        dt: Update timestamp (milliseconds)
        is_read: Whether message is read
        is_flagged: Whether message is flagged
        
    Returns:
        Created MailMessage instance
    """
    try:
        # Set current timestamp if ct or dt is 0
        now = get_now_timestamp_ms()
        if ct == 0:
            ct = now
        if dt == 0:
            dt = now
        
        return MailMessage.objects.using('mailserver_rw').create(
            account_id=account_id,
            mailbox_id=mailbox_id,
            message_id=message_id,
            subject=subject,
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            text_body=text_body,
            html_body=html_body,
            mt=mt,
            size=size,
            raw_message=raw_message,
            ct=ct,
            dt=dt,
            is_read=is_read,
            is_flagged=is_flagged
        )
    except Exception as e:
        logger.exception(f"[create_mail_message] Error creating message: {e}")
        raise


def get_mail_message_by_id(message_id: int) -> Optional[MailMessage]:
    """
    Get mail message by ID
    
    Args:
        message_id: MailMessage ID
        
    Returns:
        MailMessage instance or None if not found
    """
    try:
        return MailMessage.objects.using('mailserver_rw').get(id=message_id)
    except MailMessage.DoesNotExist:
        return None
    except Exception as e:
        logger.exception(f"[get_mail_message_by_id] Error getting message: {e}")
        return None


def get_messages_by_mailbox(
        mailbox_id: int,
        order_by: str = 'mt'
) -> List[MailMessage]:
    """
    Get messages by mailbox ID
    
    Args:
        mailbox_id: Mailbox ID
        order_by: Field to order by (default: 'mt')
        
    Returns:
        List of MailMessage instances
    """
    try:
        query = MailMessage.objects.using('mailserver_rw').filter(mailbox_id=mailbox_id)
        return list(query.order_by(order_by))
    except Exception as e:
        logger.exception(f"[get_messages_by_mailbox] Error getting messages: {e}")
        return []


def count_messages_by_mailbox(mailbox_id: int) -> int:
    """
    Count messages in mailbox
    
    Args:
        mailbox_id: Mailbox ID
        
    Returns:
        Number of messages
    """
    try:
        query = MailMessage.objects.using('mailserver_rw').filter(mailbox_id=mailbox_id)
        return query.count()
    except Exception as e:
        logger.exception(f"[count_messages_by_mailbox] Error counting messages: {e}")
        return 0


def count_unread_messages_by_mailbox(mailbox_id: int) -> int:
    """
    Count unread messages in mailbox
    
    Args:
        mailbox_id: Mailbox ID
        
    Returns:
        Number of unread messages
    """
    try:
        query = MailMessage.objects.using('mailserver_rw').filter(
            mailbox_id=mailbox_id,
            is_read=False
        )
        return query.count()
    except Exception as e:
        logger.exception(f"[count_unread_messages_by_mailbox] Error counting unread messages: {e}")
        return 0


def update_message_read_status(mailbox_id: int, message_id: int, is_read: bool) -> int:
    """
    Update message read status
    
    Args:
        mailbox_id: Mailbox ID
        message_id: Message ID
        is_read: Read status
        
    Returns:
        Number of rows updated
    """
    try:
        return MailMessage.objects.using('mailserver_rw').filter(
            mailbox_id=mailbox_id,
            id=message_id
        ).update(is_read=is_read)
    except Exception as e:
        logger.exception(f"[update_message_read_status] Error updating read status: {e}")
        raise


def delete_mail_message(message_id: int) -> bool:
    """
    Delete mail message
    
    Args:
        message_id: MailMessage ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        MailMessage.objects.using('mailserver_rw').filter(id=message_id).delete()
        return True
    except Exception as e:
        logger.exception(f"[delete_mail_message] Error deleting message: {e}")
        return False
