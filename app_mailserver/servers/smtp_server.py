"""
SMTP server implementation

This module implements an SMTP server using aiosmtpd to receive emails
and store them using the mail storage service.
"""
import logging
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, Session, Envelope
from typing import Optional

from asgiref.sync import sync_to_async

from app_mailserver.config import get_app_config
from app_mailserver.models.mail_account import MailAccount
from app_mailserver.repos import (
    get_account_by_username_any,
    create_account,
)
from app_mailserver.services.mail_storage_service import MailStorageService

logger = logging.getLogger(__name__)


class SMTPHandler:
    """SMTP handler for processing incoming emails"""

    def __init__(self):
        self.storage_service = MailStorageService()

    async def handle_DATA(
            self,
            server: SMTP,
            session: Session,
            envelope: Envelope
    ) -> str:
        """
        Handle incoming email data
        
        Args:
            server: SMTP server instance
            session: SMTP session
            envelope: Email envelope (contains From, To, etc.)
            
        Returns:
            Response string (typically '250 Message accepted for delivery')
        """
        try:
            # Get recipient address
            if not envelope.rcpt_tos:
                logger.warning("[handle_DATA] No recipients in envelope")
                return '550 No recipients'

            recipient = envelope.rcpt_tos[0]  # Use first recipient for now

            # Find or create mail account for recipient
            account = await self._get_or_create_account(recipient)

            # Get email data
            email_data = envelope.content

            # Store email in INBOX
            mail_message = await sync_to_async(self.storage_service.store_mail)(
                account=account,
                mailbox_name='INBOX',
                email_data=email_data,
                recipient_address=recipient
            )

            logger.info(f"[handle_DATA] Stored email: id={mail_message.id}, "
                        f"from={envelope.mail_from}, to={recipient}")

            return '250 Message accepted for delivery'

        except Exception as e:
            logger.exception(f"[handle_DATA] Failed to process email: {e}")
            return '550 Error processing message'

    async def _get_or_create_account(self, email_address: str) -> MailAccount:
        """Get or create mail account for email address"""
        try:
            # Extract domain from email
            if '@' in email_address:
                username, domain = email_address.split('@', 1)
            else:
                username = email_address
                domain = 'localhost'

            # Try to get existing account
            account = await sync_to_async(get_account_by_username_any)(email_address)

            if not account:
                # Create new account
                import time
                now = int(time.time() * 1000)
                account = await sync_to_async(create_account)(
                    username=email_address,
                    password='',  # No password for incoming mail
                    domain=domain,
                    is_active=True,
                    ct=now,
                    ut=now
                )
                logger.info(f"[_get_or_create_account] Created new account: {email_address}")

            return account

        except Exception as e:
            logger.exception(f"[_get_or_create_account] Failed to get/create account: {e}")
            raise


class SMTPServer:
    """SMTP server wrapper"""

    def __init__(self):
        self.config = get_app_config()
        self.host = self.config.get('server_host', '0.0.0.0')
        self.port = self.config.get('smtp_port', 25)
        self.controller: Optional[Controller] = None

    def start(self):
        """Start SMTP server"""
        try:
            handler = SMTPHandler()
            self.controller = Controller(
                handler,
                hostname=self.host,
                port=self.port
            )
            self.controller.start()
            logger.info(f"[SMTPServer] Started SMTP server on {self.host}:{self.port}")
        except Exception as e:
            logger.exception(f"[SMTPServer] Failed to start SMTP server: {e}")
            raise

    def stop(self):
        """Stop SMTP server"""
        if self.controller:
            self.controller.stop()
            logger.info("[SMTPServer] Stopped SMTP server")
