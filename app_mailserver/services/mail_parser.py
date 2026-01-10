"""
Mail parsing service

This service parses email messages and extracts:
- Email metadata (From, To, Subject, Date, etc.)
- Email body (text and HTML)
- Attachments (filename, content, MIME type)
"""
from email import message_from_bytes

import logging
from datetime import datetime
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Dict, List, Any, Optional, Tuple

from common.components.singleton import Singleton

logger = logging.getLogger(__name__)


class MailParser(Singleton):
    """Mail parser service"""

    @staticmethod
    def parse_email(email_data: bytes) -> Dict[str, Any]:
        """
        Parse email message from bytes
        
        Args:
            email_data: Raw email data as bytes
            
        Returns:
            Dictionary containing parsed email data:
            - message_id: Message-ID header
            - subject: Subject
            - from_address: From address
            - to_addresses: List of To addresses
            - cc_addresses: List of CC addresses
            - bcc_addresses: List of BCC addresses
            - date: Date as datetime
            - text_body: Plain text body
            - html_body: HTML body
            - attachments: List of attachment dictionaries
            - raw_message: Original email data as string
        """
        try:
            # Parse email message
            msg = message_from_bytes(email_data)

            # Extract headers
            message_id = msg.get('Message-ID', '').strip()
            subject = msg.get('Subject', '').strip()
            from_address = msg.get('From', '').strip()
            to_addresses = msg.get('To', '').strip()
            cc_addresses = msg.get('Cc', '').strip()
            bcc_addresses = msg.get('Bcc', '').strip()

            # Parse date
            date_str = msg.get('Date', '')
            date = None
            if date_str:
                try:
                    date = parsedate_to_datetime(date_str)
                except Exception as e:
                    logger.warning(f"[parse_email] Failed to parse date '{date_str}': {e}")
                    date = datetime.utcnow()
            else:
                date = datetime.utcnow()

            # Extract body and attachments
            text_body, html_body, attachments = MailParser._extract_body_and_attachments(msg)

            # Get raw message as string
            raw_message = email_data.decode('utf-8', errors='replace')

            result = {
                'message_id': message_id,
                'subject': subject,
                'from_address': from_address,
                'to_addresses': to_addresses,
                'cc_addresses': cc_addresses,
                'bcc_addresses': bcc_addresses,
                'date': date,
                'text_body': text_body,
                'html_body': html_body,
                'attachments': attachments,
                'raw_message': raw_message,
            }

            logger.info(f"[parse_email] Parsed email: message_id={message_id}, subject={subject}, "
                        f"attachments={len(attachments)}")

            return result

        except Exception as e:
            logger.exception(f"[parse_email] Failed to parse email: {e}")
            raise

    @staticmethod
    def _extract_body_and_attachments(msg: Message) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Recursively extract body and attachments from email message
        
        Args:
            msg: Email message object
            
        Returns:
            Tuple of (text_body, html_body, attachments)
        """
        text_body = ""
        html_body = ""
        attachments = []

        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = part.get('Content-Disposition', '')

                # Skip multipart containers
                if content_type.startswith('multipart/'):
                    continue

                # Handle attachments
                if 'attachment' in content_disposition or 'inline' in content_disposition:
                    attachment_data = MailParser._extract_attachment(part)
                    if attachment_data:
                        attachments.append(attachment_data)
                # Handle body content
                elif content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text_body += payload.decode('utf-8', errors='replace')
                    except Exception as e:
                        logger.warning(f"[_extract_body_and_attachments] Failed to decode text body: {e}")
                elif content_type == 'text/html':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_body += payload.decode('utf-8', errors='replace')
                    except Exception as e:
                        logger.warning(f"[_extract_body_and_attachments] Failed to decode HTML body: {e}")
        else:
            # Handle simple (non-multipart) messages
            content_type = msg.get_content_type()
            content_disposition = msg.get('Content-Disposition', '')

            if 'attachment' in content_disposition:
                attachment_data = MailParser._extract_attachment(msg)
                if attachment_data:
                    attachments.append(attachment_data)
            elif content_type == 'text/plain':
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        text_body += payload.decode('utf-8', errors='replace')
                except Exception as e:
                    logger.warning(f"[_extract_body_and_attachments] Failed to decode text body: {e}")
            elif content_type == 'text/html':
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        html_body += payload.decode('utf-8', errors='replace')
                except Exception as e:
                    logger.warning(f"[_extract_body_and_attachments] Failed to decode HTML body: {e}")

        return text_body, html_body, attachments

    @staticmethod
    def _extract_attachment(part: Message) -> Optional[Dict[str, Any]]:
        """
        Extract attachment data from email part
        
        Args:
            part: Email message part
            
        Returns:
            Dictionary with attachment data, or None if extraction fails
        """
        try:
            # Get filename
            filename = part.get_filename()
            if not filename:
                # Try to get filename from Content-Disposition header
                content_disposition = part.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    # Extract filename from Content-Disposition
                    import re
                    match = re.search(r'filename="?([^"]+)"?', content_disposition)
                    if match:
                        filename = match.group(1)
                    else:
                        # Try without quotes
                        match = re.search(r'filename=([^;]+)', content_disposition)
                        if match:
                            filename = match.group(1).strip()

            if not filename:
                # Generate default filename
                content_type = part.get_content_type()
                extension = MailParser._get_extension_from_content_type(content_type)
                filename = f"attachment{extension}"

            # Get content type
            content_type = part.get_content_type() or 'application/octet-stream'

            # Get content disposition
            content_disposition = part.get('Content-Disposition', 'attachment')

            # Get Content-ID (for inline images)
            content_id = part.get('Content-ID', '').strip('<>')

            # Get attachment data
            payload = part.get_payload(decode=True)
            if not payload:
                return None

            return {
                'filename': filename,
                'content_type': content_type,
                'content_disposition': content_disposition,
                'content_id': content_id,
                'data': payload,
                'size': len(payload)
            }

        except Exception as e:
            logger.warning(f"[_extract_attachment] Failed to extract attachment: {e}")
            return None

    @staticmethod
    def _get_extension_from_content_type(content_type: str) -> str:
        """Get file extension from MIME content type"""
        extension_map = {
            'text/plain': '.txt',
            'text/html': '.html',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'application/pdf': '.pdf',
            'application/zip': '.zip',
            'application/json': '.json',
        }
        return extension_map.get(content_type, '.bin')
