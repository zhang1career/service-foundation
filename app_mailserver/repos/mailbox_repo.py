"""
Mailbox repository

This module provides database operations for Mailbox model.
"""
import logging
from typing import Optional, List, Tuple

from app_mailserver.models.mailbox import Mailbox

logger = logging.getLogger(__name__)


def get_mailbox_by_account_and_path(account_id: int, path: str) -> Optional[Mailbox]:
    """
    Get mailbox by account ID and path
    
    Args:
        account_id: Account ID
        path: Mailbox path (e.g., 'INBOX')
        
    Returns:
        Mailbox instance or None if not found
    """
    try:
        return Mailbox.objects.using('mailserver_rw').filter(
            account_id=account_id,
            path=path
        ).first()
    except Exception as e:
        logger.exception(f"[get_mailbox_by_account_and_path] Error getting mailbox: {e}")
        return None


def get_mailboxes_by_account(account_id: int) -> List[Mailbox]:
    """
    Get all mailboxes for an account
    
    Args:
        account_id: Account ID
        
    Returns:
        List of Mailbox instances
    """
    try:
        return list(Mailbox.objects.using('mailserver_rw').filter(account_id=account_id))
    except Exception as e:
        logger.exception(f"[get_mailboxes_by_account] Error getting mailboxes: {e}")
        return []


def get_or_create_mailbox(
        account_id: int,
        path: str,
        name: str = None,
        ct: int = 0,
        ut: int = 0
) -> Tuple[Mailbox, bool]:
    """
    Get or create mailbox for account
    
    Args:
        account_id: Account ID
        path: Mailbox path (e.g., 'INBOX')
        name: Mailbox name (defaults to last part of path)
        ct: Create timestamp (milliseconds)
        ut: Update timestamp (milliseconds)
        
    Returns:
        Tuple of (Mailbox instance, created flag)
    """
    try:
        if name is None:
            name = path.split('.')[-1] if '.' in path else path

        return Mailbox.objects.using('mailserver_rw').get_or_create(
            account_id=account_id,
            path=path,
            defaults={
                'name': name,
                'ct': ct,
                'ut': ut
            }
        )
    except Exception as e:
        logger.exception(f"[get_or_create_mailbox] Error getting/creating mailbox: {e}")
        raise


def get_mailbox_by_id(mailbox_id: int) -> Optional[Mailbox]:
    """
    Get mailbox by ID
    
    Args:
        mailbox_id: Mailbox ID
        
    Returns:
        Mailbox instance or None if not found
    """
    try:
        return Mailbox.objects.using('mailserver_rw').get(id=mailbox_id)
    except Mailbox.DoesNotExist:
        return None
    except Exception as e:
        logger.exception(f"[get_mailbox_by_id] Error getting mailbox: {e}")
        return None


def update_mailbox(mailbox: Mailbox, **kwargs) -> int:
    """
    Update mailbox fields
    
    Args:
        mailbox: Mailbox instance to update
        **kwargs: Fields to update
        
    Returns:
        Number of rows updated
    """
    try:
        return Mailbox.objects.using('mailserver_rw').filter(id=mailbox.id).update(**kwargs)
    except Exception as e:
        logger.exception(f"[update_mailbox] Error updating mailbox: {e}")
        raise
