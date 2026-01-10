"""
Mail storage service

This service handles storing and retrieving emails:
- Stores email body and metadata in database
- Stores attachments in OSS
- Maintains mapping between emails and attachments
"""
import logging
import time
import uuid
from datetime import datetime
from django.db import transaction
from typing import Dict, Any, Optional

from app_mailserver.models.mail_account import MailAccount
from app_mailserver.models.mail_message import MailMessage
from app_mailserver.models.mailbox import Mailbox
from app_mailserver.repos import (
    get_or_create_mailbox,
    create_mail_message,
    count_messages_by_mailbox,
    get_mailbox_by_id,
    update_mailbox,
    create_mail_attachment,
    get_mail_message_by_id,
    get_attachments_by_message,
    get_attachment_by_id,
    delete_attachments_by_message,
    delete_mail_message,
)
from app_mailserver.services.mail_parser import MailParser
from app_mailserver.services.oss_integration_service import OSSIntegrationService
from common.components.singleton import Singleton
from common.enums.content_type_enum import ContentTypeEnum

logger = logging.getLogger(__name__)


class MailStorageService(Singleton):
    """Mail storage service"""

    def __init__(self):
        self.oss_service = OSSIntegrationService()
        self.parser = MailParser()

    def store_mail(
            self,
            account: MailAccount,
            mailbox_name: str,
            email_data: bytes,
            recipient_address: Optional[str] = None
    ) -> MailMessage:
        """
        Store email message and attachments
        
        Args:
            account: Mail account that received the email
            mailbox_name: Name of the mailbox (e.g., 'INBOX')
            email_data: Raw email data as bytes
            recipient_address: Optional recipient address (for routing)
            
        Returns:
            Created MailMessage instance
        """
        try:
            # Parse email
            parsed = self.parser.parse_email(email_data)

            # Get or create mailbox
            mailbox = self._get_or_create_mailbox(account, mailbox_name)

            # Calculate email size
            email_size = len(email_data)

            # Create mail message in database
            with transaction.atomic():
                # Convert datetime to UNIX timestamp (milliseconds)
                mt = int(parsed['date'].timestamp() * 1000) if isinstance(parsed['date'], datetime) else int(
                    time.time() * 1000)
                ct = int(time.time() * 1000)

                mail_message = create_mail_message(
                    account_id=account.id,
                    mailbox_id=mailbox.id,
                    message_id=parsed['message_id'] or self._generate_message_id(),
                    subject=parsed['subject'],
                    from_address=parsed['from_address'],
                    to_addresses=parsed['to_addresses'],
                    cc_addresses=parsed['cc_addresses'],
                    bcc_addresses=parsed['bcc_addresses'],
                    text_body=parsed['text_body'],
                    html_body=parsed['html_body'],
                    mt=mt,
                    size=email_size,
                    raw_message=parsed['raw_message'],
                    ct=ct,
                    dt=ct
                )

                # Store attachments
                for attachment_data in parsed['attachments']:
                    self._store_attachment(mail_message, attachment_data)

                # Update mailbox message count
                message_count = count_messages_by_mailbox(mailbox.id)
                update_mailbox(mailbox, message_count=message_count, dt=int(time.time() * 1000))

            logger.info(f"[store_mail] Stored email: id={mail_message.id}, "
                        f"message_id={mail_message.message_id}, "
                        f"attachments={len(parsed['attachments'])}")

            return mail_message

        except Exception as e:
            logger.exception(f"[store_mail] Failed to store email: {e}")
            raise

    def _get_or_create_mailbox(self, account: MailAccount, mailbox_name: str) -> Mailbox:
        """Get or create mailbox for account"""
        ct = int(time.time() * 1000)
        mailbox, created = get_or_create_mailbox(
            account_id=account.id,
            path=mailbox_name,
            name=mailbox_name.split('.')[-1] if '.' in mailbox_name else mailbox_name,
            ct=ct,
            dt=ct
        )
        if not created:
            # Update dt when mailbox is accessed
            update_mailbox(mailbox, dt=int(time.time() * 1000))
        return mailbox

    def _store_attachment(self, mail_message: MailMessage, attachment_data: Dict[str, Any]):
        """Store attachment in OSS and create database record"""
        try:
            # Generate OSS key (path)
            # Format: mail-attachments/{account_id}/{message_id}/{filename}
            account_id = mail_message.account_id
            message_id = mail_message.id
            filename = attachment_data['filename']

            # Sanitize filename for OSS key
            safe_filename = self._sanitize_filename(filename)
            oss_key = f"{account_id}/{message_id}/{safe_filename}"

            # Convert MIME type string to ContentTypeEnum ID
            mime_type = attachment_data['content_type']
            content_type_enum = ContentTypeEnum.from_mime_type(mime_type)
            content_type_id = content_type_enum.value

            # Upload to OSS (still use MIME type string for OSS)
            upload_result = self.oss_service.upload_attachment(
                key=oss_key,
                data=attachment_data['data'],
                content_type=mime_type,  # OSS still uses MIME type string
                metadata={
                    'message_id': str(mail_message.id),
                    'filename': filename,
                }
            )

            # Create attachment record in database (store enum ID)
            ct = int(time.time() * 1000)
            create_mail_attachment(
                message_id=mail_message.id,
                filename=filename,
                content_type=content_type_id,  # Store enum ID
                size=attachment_data['size'],
                oss_bucket=upload_result['bucket'],
                oss_key=upload_result['key'],
                content_id=attachment_data.get('content_id', ''),
                content_disposition=attachment_data.get('content_disposition', 'attachment'),
                ct=ct
            )

            logger.debug(f"[_store_attachment] Stored attachment: {filename}, "
                         f"oss_key={oss_key}, size={attachment_data['size']}")

        except Exception as e:
            logger.exception(f"[_store_attachment] Failed to store attachment: {e}")
            # Don't fail the entire email storage if attachment fails
            # Just log the error

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for use in OSS key"""
        import re
        # Remove or replace invalid characters
        safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Limit length
        if len(safe) > 255:
            name, ext = safe.rsplit('.', 1) if '.' in safe else (safe, '')
            safe = name[:250] + ('.' + ext if ext else '')
        return safe

    def _generate_message_id(self) -> str:
        """Generate a unique message ID if not present in email"""
        return f"<{uuid.uuid4()}@mailserver>"

    def retrieve_mail(self, message_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete email message with attachments
        
        Args:
            message_id: MailMessage ID
            
        Returns:
            Dictionary with email data and attachments, or None if not found
        """
        try:
            mail_message = get_mail_message_by_id(message_id)
            if not mail_message:
                logger.warning(f"[retrieve_mail] Message not found: id={message_id}")
                return None

            # Get attachments
            attachments = []
            for attachment in get_attachments_by_message(mail_message.id):
                # Convert enum ID to MIME type string
                try:
                    content_type_enum = ContentTypeEnum(attachment.content_type)
                    mime_type = content_type_enum.to_mime_type()
                except (ValueError, AttributeError):
                    # Fallback to default if enum value is invalid
                    mime_type = 'application/octet-stream'

                attachments.append({
                    'id': attachment.id,
                    'filename': attachment.filename,
                    'content_type': mime_type,  # Return MIME type string
                    'size': attachment.size,
                    'content_id': attachment.content_id,
                    'content_disposition': attachment.content_disposition,
                })

            return {
                'message': mail_message,
                'attachments': attachments,
            }

        except Exception as e:
            logger.exception(f"[retrieve_mail] Failed to retrieve message: {e}")
            return None

    def get_attachment_data(self, attachment_id: int) -> Optional[bytes]:
        """
        Get attachment data from OSS
        
        Args:
            attachment_id: MailAttachment ID
            
        Returns:
            Attachment data as bytes, or None if not found
        """
        try:
            attachment = get_attachment_by_id(attachment_id)
            if not attachment:
                logger.warning(f"[get_attachment_data] Attachment not found: id={attachment_id}")
                return None

            data = self.oss_service.download_attachment(attachment.oss_key)

            logger.debug(f"[get_attachment_data] Retrieved attachment: id={attachment_id}, "
                         f"filename={attachment.filename}, size={len(data)}")

            return data

        except Exception as e:
            logger.exception(f"[get_attachment_data] Failed to get attachment: {e}")
            return None

    def delete_mail(self, message_id: int) -> bool:
        """
        Delete email message and its attachments
        
        Args:
            message_id: MailMessage ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with transaction.atomic():
                mail_message = get_mail_message_by_id(message_id)
                if not mail_message:
                    logger.warning(f"[delete_mail] Message not found: id={message_id}")
                    return False

                # Delete attachments from OSS
                attachments = get_attachments_by_message(mail_message.id)
                for attachment in attachments:
                    self.oss_service.delete_attachment(attachment.oss_key)

                # Delete attachment records
                delete_attachments_by_message(mail_message.id)

                # Delete mail message
                mailbox_id = mail_message.mailbox_id
                delete_mail_message(message_id)

                # Update mailbox message count
                mailbox = get_mailbox_by_id(mailbox_id)
                if mailbox:
                    message_count = count_messages_by_mailbox(mailbox_id)
                    update_mailbox(mailbox, message_count=message_count, dt=int(time.time() * 1000))

            logger.info(f"[delete_mail] Deleted email: id={message_id}")
            return True

        except Exception as e:
            logger.exception(f"[delete_mail] Failed to delete message: {e}")
            return False
