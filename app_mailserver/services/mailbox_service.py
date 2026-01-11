"""
Mailbox service

This service handles business logic for mailbox operations:
- Parameter validation and transformation
- Business rule enforcement
- Data transformation (Model -> Dict)
- Error handling
"""
import logging
import time
from typing import Dict, Any, Optional

from app_mailserver.repos import (
    get_mailbox_by_id,
    get_mailboxes_by_account,
    get_account_by_id,
    get_mailbox_by_account_and_path,
    create_mailbox,
    update_mailbox,
    delete_mailbox,
)
from common.components.singleton import Singleton

logger = logging.getLogger(__name__)


def _mailbox_to_dict(mailbox) -> Dict[str, Any]:
    """
    Convert Mailbox model instance to dictionary

    Args:
        mailbox: Mailbox model instance

    Returns:
        Mailbox dictionary
    """
    return {
        'id': mailbox.id,
        'account_id': mailbox.account_id,
        'name': mailbox.name,
        'path': mailbox.path,
        'message_count': mailbox.message_count,
        'unread_count': mailbox.unread_count,
        'ct': mailbox.ct,
        'ut': mailbox.ut,
    }


class MailboxService(Singleton):
    """Mailbox service"""

    def list_mailboxes(
            self,
            account_id: int,
            offset: int = 0,
            limit: int = 1000,
    ) -> Dict[str, Any]:
        """
        List mailboxes for an account
        
        Args:
            account_id: Account ID
            offset: Pagination offset (default: 0)
            limit: Pagination limit (default: 1000, max: 1000)
            
        Returns:
            Dictionary with paginated mailbox data including:
            - data: List of mailbox dictionaries
            - total_num: Total number of mailboxes
            - next_offset: Next offset for pagination (None if last page)
            
        Raises:
            ValueError: If account_id is invalid or account not found
        """
        try:
            # Validate account exists
            account = get_account_by_id(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found")

            # Validate and adjust limit
            if limit <= 0:
                limit = 1000
            if limit > 1000:
                limit = 1000

            # Get mailboxes
            mailboxes = get_mailboxes_by_account(account_id)

            # Apply pagination
            total_num = len(mailboxes)
            start_idx = offset
            end_idx = offset + limit

            paginated_mailboxes = mailboxes[start_idx:end_idx]

            # Convert to dict list
            mailboxes_data = []
            for mailbox in paginated_mailboxes:
                mailboxes_data.append(_mailbox_to_dict(mailbox))

            # Calculate next offset
            next_offset = end_idx if end_idx < total_num else None

            return {
                'data': mailboxes_data,
                'total_num': total_num,
                'next_offset': next_offset,
            }

        except ValueError as e:
            logger.warning(f"[MailboxService.list_mailboxes] Validation error: {e}")
            raise
        except Exception as e:
            logger.exception(f"[MailboxService.list_mailboxes] Error listing mailboxes: {e}")
            raise

    def get_mailbox(self, mailbox_id: int) -> Optional[Dict[str, Any]]:
        """
        Get mailbox by ID
        
        Args:
            mailbox_id: Mailbox ID
            
        Returns:
            Mailbox dictionary or None if not found
        """
        try:
            mailbox = get_mailbox_by_id(mailbox_id)
            if not mailbox:
                return None

            return _mailbox_to_dict(mailbox)

        except Exception as e:
            logger.exception(f"[MailboxService.get_mailbox] Error getting mailbox: {e}")
            raise

    def create_mailbox(
            self,
            account_id: int,
            name: str,
            path: str,
            message_count: int = 0,
            unread_count: int = 0
    ) -> Dict[str, Any]:
        """
        Create a new mailbox
        
        Args:
            account_id: Account ID
            name: Mailbox name (e.g., 'INBOX', 'Sent')
            path: Mailbox path (e.g., 'INBOX', 'INBOX.Sent')
            message_count: Number of messages (optional, defaults to 0)
            unread_count: Number of unread messages (optional, defaults to 0)
            
        Returns:
            Created mailbox dictionary
            
        Raises:
            ValueError: If account_id is invalid, account not found, or mailbox already exists
        """
        try:
            # Validate account exists
            account = get_account_by_id(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found")

            # Validate required fields
            name = name.strip() if name else ''
            path = path.strip() if path else ''
            
            if not name:
                raise ValueError("Name is required")
            if not path:
                raise ValueError("Path is required")

            # Check if mailbox with same account_id and path already exists
            existing = get_mailbox_by_account_and_path(account_id, path)
            if existing:
                raise ValueError(f"Mailbox with path '{path}' already exists for account {account_id}")

            # Create mailbox
            mailbox = create_mailbox(
                account_id=account_id,
                name=name,
                path=path,
                message_count=message_count,
                unread_count=unread_count
            )

            return _mailbox_to_dict(mailbox)

        except ValueError as e:
            logger.warning(f"[MailboxService.create_mailbox] Validation error: {e}")
            raise
        except Exception as e:
            logger.exception(f"[MailboxService.create_mailbox] Error creating mailbox: {e}")
            # Check for unique constraint violations
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                raise ValueError(f"Mailbox with path '{path}' already exists for account {account_id}")
            raise

    def update_mailbox(
            self,
            mailbox_id: int,
            name: Optional[str] = None,
            path: Optional[str] = None,
            message_count: Optional[int] = None,
            unread_count: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update mailbox
        
        Args:
            mailbox_id: Mailbox ID
            name: New mailbox name (optional)
            path: New mailbox path (optional)
            message_count: New message count (optional)
            unread_count: New unread count (optional)
            
        Returns:
            Updated mailbox dictionary or None if mailbox not found
            
        Raises:
            ValueError: If validation fails or path conflict exists
        """
        try:
            mailbox = get_mailbox_by_id(mailbox_id)
            if not mailbox:
                return None

            # Prepare update fields
            update_fields = {}
            
            if name is not None:
                name = name.strip() if name else ''
                if not name:
                    raise ValueError("Name cannot be empty")
                update_fields['name'] = name

            if path is not None:
                path = path.strip() if path else ''
                if not path:
                    raise ValueError("Path cannot be empty")
                # Check if path conflict exists (only if path is being changed)
                if path != mailbox.path:
                    existing = get_mailbox_by_account_and_path(mailbox.account_id, path)
                    if existing and existing.id != mailbox_id:
                        raise ValueError(f"Mailbox with path '{path}' already exists for account {mailbox.account_id}")
                update_fields['path'] = path

            if message_count is not None:
                if message_count < 0:
                    raise ValueError("Message count cannot be negative")
                update_fields['message_count'] = message_count

            if unread_count is not None:
                if unread_count < 0:
                    raise ValueError("Unread count cannot be negative")
                update_fields['unread_count'] = unread_count

            # Update timestamp
            update_fields['ut'] = int(time.time() * 1000)

            # Perform update
            if update_fields:
                update_mailbox(mailbox, **update_fields)
                # Reload mailbox to get updated data
                mailbox = get_mailbox_by_id(mailbox_id)

            return _mailbox_to_dict(mailbox)

        except ValueError as e:
            logger.warning(f"[MailboxService.update_mailbox] Validation error: {e}")
            raise
        except Exception as e:
            logger.exception(f"[MailboxService.update_mailbox] Error updating mailbox: {e}")
            # Check for unique constraint violations
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                raise ValueError(f"Mailbox with path '{path}' already exists")
            raise

    def delete_mailbox(self, mailbox_id: int) -> bool:
        """
        Delete mailbox (hard delete)
        
        Args:
            mailbox_id: Mailbox ID
            
        Returns:
            True if deleted successfully, False if mailbox not found
        """
        try:
            mailbox = get_mailbox_by_id(mailbox_id)
            if not mailbox:
                return False

            # Delete mailbox
            success = delete_mailbox(mailbox_id)
            return success

        except Exception as e:
            logger.exception(f"[MailboxService.delete_mailbox] Error deleting mailbox: {e}")
            raise
