"""
Mail attachment repository

This module provides database operations for MailAttachment model.
"""
import logging
from typing import Optional, List

from app_mailserver.models.mail_attachment import MailAttachment

logger = logging.getLogger(__name__)


def create_mail_attachment(
        message_id: int,
        filename: str,
        content_type: int,
        size: int,
        oss_bucket: str,
        oss_key: str,
        content_id: str = '',
        content_disposition: str = 'attachment',
        ct: int = 0
) -> MailAttachment:
    """
    Create a new mail attachment
    
    Args:
        message_id: Message ID
        filename: Attachment filename
        content_type: ContentTypeEnum ID
        size: Attachment size in bytes
        oss_bucket: OSS bucket name
        oss_key: OSS key (path)
        content_id: Content-ID (for inline images)
        content_disposition: Content-Disposition (attachment or inline)
        ct: Create timestamp (milliseconds)
        
    Returns:
        Created MailAttachment instance
    """
    try:
        return MailAttachment.objects.using('mailserver_rw').create(
            message_id=message_id,
            filename=filename,
            content_type=content_type,
            size=size,
            oss_bucket=oss_bucket,
            oss_key=oss_key,
            content_id=content_id,
            content_disposition=content_disposition,
            ct=ct
        )
    except Exception as e:
        logger.exception(f"[create_mail_attachment] Error creating attachment: {e}")
        raise


def get_attachment_by_id(attachment_id: int) -> Optional[MailAttachment]:
    """
    Get attachment by ID
    
    Args:
        attachment_id: MailAttachment ID
        
    Returns:
        MailAttachment instance or None if not found
    """
    try:
        return MailAttachment.objects.using('mailserver_rw').get(id=attachment_id)
    except MailAttachment.DoesNotExist:
        return None
    except Exception as e:
        logger.exception(f"[get_attachment_by_id] Error getting attachment: {e}")
        return None


def get_attachments_by_message(message_id: int) -> List[MailAttachment]:
    """
    Get all attachments for a message
    
    Args:
        message_id: Message ID
        
    Returns:
        List of MailAttachment instances
    """
    try:
        return list(MailAttachment.objects.using('mailserver_rw').filter(message_id=message_id))
    except Exception as e:
        logger.exception(f"[get_attachments_by_message] Error getting attachments: {e}")
        return []


def delete_attachments_by_message(message_id: int) -> int:
    """
    Delete all attachments for a message
    
    Args:
        message_id: Message ID
        
    Returns:
        Number of attachments deleted
    """
    try:
        count, _ = MailAttachment.objects.using('mailserver_rw').filter(message_id=message_id).delete()
        return count
    except Exception as e:
        logger.exception(f"[delete_attachments_by_message] Error deleting attachments: {e}")
        return 0
