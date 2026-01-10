"""
Mail account repository

This module provides database operations for MailAccount model.
"""
import logging
import time
from typing import Optional, Dict, Any

from app_mailserver.models.mail_account import MailAccount

logger = logging.getLogger(__name__)


def get_account_by_id(account_id: int) -> Optional[MailAccount]:
    """
    Get mail account by ID
    
    Args:
        account_id: Account ID
        
    Returns:
        MailAccount instance or None if not found
    """
    try:
        return MailAccount.objects.using('mailserver_rw').filter(id=account_id).first()
    except Exception as e:
        logger.exception(f"[get_account_by_id] Error getting account: {e}")
        return None


def get_account_by_username(username: str, is_active: bool = True) -> Optional[MailAccount]:
    """
    Get mail account by username
    
    Args:
        username: Account username (email address)
        is_active: Whether to filter by active status
        
    Returns:
        MailAccount instance or None if not found
    """
    try:
        query = MailAccount.objects.using('mailserver_rw').filter(username=username)
        if is_active:
            query = query.filter(is_active=True)
        return query.first()
    except Exception as e:
        logger.exception(f"[get_account_by_username] Error getting account: {e}")
        return None


def get_account_by_username_any(username: str) -> Optional[MailAccount]:
    """
    Get mail account by username (any status)
    
    Args:
        username: Account username (email address)
        
    Returns:
        MailAccount instance or None if not found
    """
    try:
        return MailAccount.objects.using('mailserver_rw').filter(username=username).first()
    except Exception as e:
        logger.exception(f"[get_account_by_username_any] Error getting account: {e}")
        return None


def list_accounts(
        offset: int = 0,
        limit: int = 20,
        domain: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
) -> Dict[str, Any]:
    """
    List mail accounts with pagination and filtering
    
    Args:
        offset: Offset for pagination
        limit: Limit for pagination
        domain: Filter by domain (optional)
        is_active: Filter by active status (optional)
        search: Search keyword for username (optional)
        
    Returns:
        Dictionary with 'accounts' (list) and 'total' (int)
    """
    try:
        query = MailAccount.objects.using('mailserver_rw').all()

        # Apply filters
        if domain:
            query = query.filter(domain=domain)

        if is_active is not None:
            query = query.filter(is_active=is_active)

        if search:
            query = query.filter(username__icontains=search)

        # Get total count
        total = query.count()

        # Apply pagination
        accounts = query.order_by('-ct')[offset:offset + limit]

        return {
            'accounts': list(accounts),
            'total': total
        }
    except Exception as e:
        logger.exception(f"[list_accounts] Error listing accounts: {e}")
        raise


def create_account(
        username: str,
        password: str = '',
        domain: str = 'localhost',
        is_active: bool = True,
        ct: int = 0,
        dt: int = 0
) -> MailAccount:
    """
    Create a new mail account
    
    Args:
        username: Account username (email address)
        password: Account password
        domain: Domain name
        is_active: Whether account is active
        ct: Create timestamp (milliseconds)
        dt: Update timestamp (milliseconds)
        
    Returns:
        Created MailAccount instance
    """
    try:
        if ct == 0:
            ct = int(time.time() * 1000)
        if dt == 0:
            dt = ct

        # Extract domain from username if not provided
        if domain == 'localhost' and '@' in username:
            domain = username.split('@', 1)[1]

        return MailAccount.objects.using('mailserver_rw').create(
            username=username,
            password=password,
            domain=domain,
            is_active=is_active,
            ct=ct,
            dt=dt
        )
    except Exception as e:
        logger.exception(f"[create_account] Error creating account: {e}")
        raise


def update_account(
        account_id: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        domain: Optional[str] = None,
        is_active: Optional[bool] = None
) -> Optional[MailAccount]:
    """
    Update mail account
    
    Args:
        account_id: Account ID
        username: New username (optional)
        password: New password (optional)
        domain: New domain (optional)
        is_active: New active status (optional)
        
    Returns:
        Updated MailAccount instance or None if not found
    """
    try:
        account = get_account_by_id(account_id)
        if not account:
            return None

        update_fields = []

        if username is not None:
            account.username = username
            update_fields.append('username')

        if password is not None:
            account.password = password
            update_fields.append('password')

        if domain is not None:
            account.domain = domain
            update_fields.append('domain')

        if is_active is not None:
            account.is_active = is_active
            update_fields.append('is_active')

        if update_fields:
            account.ut = int(time.time() * 1000)
            update_fields.append('dt')
            # 显式指定数据库以确保更新操作在正确的数据库上执行
            account.save(using='mailserver_rw', update_fields=update_fields)

        return account
    except Exception as e:
        logger.exception(f"[update_account] Error updating account: {e}")
        raise


def delete_account(account_id: int) -> bool:
    """
    Delete mail account (hard delete)
    
    Args:
        account_id: Account ID
        
    Returns:
        True if deleted successfully, False if account not found
    """
    try:
        account = get_account_by_id(account_id)
        if not account:
            return False

        # 显式指定数据库以确保删除操作在正确的数据库上执行
        account.delete(using='mailserver_rw')
        return True
    except Exception as e:
        logger.exception(f"[delete_account] Error deleting account: {e}")
        raise
