"""
Mail account service

This service handles business logic for mail account operations:
- Parameter validation and transformation
- Business rule enforcement
- Data transformation (Model -> Dict)
- Error handling
"""
import logging
from typing import Dict, Any, Optional

from app_mailserver.repos import (
    get_account_by_id,
    list_accounts,
    create_account,
    update_account,
    delete_account,
)
from app_mailserver.repos.mail_account_repo import get_account_by_username_any
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_PAGE, LIMIT_LIST
from common.consts.string_const import EMPTY_STRING
from common.utils.page_util import build_page

logger = logging.getLogger(__name__)


class MailAccountService(Singleton):
    """Mail account service"""

    def list_accounts(
            self,
            offset: int = 0,
            limit: int = LIMIT_PAGE,
            domain: Optional[str] = None,
            is_active: Optional[bool] = None,
            search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List mail accounts with pagination and filtering
        
        Args:
            offset: Pagination offset (default: 0)
            limit: Pagination limit (default: 20, max: 1000)
            domain: Filter by domain (optional)
            is_active: Filter by active status (optional, true/false)
            search: Search keyword for username (optional)
            
        Returns:
            Dictionary with paginated account data including:
            - data: List of account dictionaries
            - total_num: Total number of accounts
            - next_offset: Next offset for pagination (None if last page)
        """
        try:
            # Validate and adjust limit
            if limit <= 0:
                limit = LIMIT_PAGE
            if limit > LIMIT_LIST:
                limit = LIMIT_LIST

            # Normalize empty strings to None
            if domain == EMPTY_STRING:
                domain = None
            if search == EMPTY_STRING:
                search = None

            # Query accounts
            result = list_accounts(
                offset=offset,
                limit=limit,
                domain=domain,
                is_active=is_active,
                search=search
            )

            # Convert accounts to dict list
            accounts_data = []
            for account in result['accounts']:
                accounts_data.append(self._account_to_dict(account))

            # Build paginated response
            next_offset = offset + limit if offset + limit < result['total'] else None
            page_data = build_page(accounts_data, next_offset, result['total'])

            return page_data

        except Exception as e:
            logger.exception(f"[MailAccountService.list_accounts] Error listing accounts: {e}")
            raise

    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Get mail account by ID
        
        Args:
            account_id: Account ID
            
        Returns:
            Account dictionary or None if not found
        """
        try:
            account = get_account_by_id(account_id)
            if not account:
                return None

            return self._account_to_dict(account)

        except Exception as e:
            logger.exception(f"[MailAccountService.get_account] Error getting account: {e}")
            raise

    def create_account(
            self,
            username: str,
            password: str = '',
            domain: str = 'localhost',
            is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new mail account
        
        Args:
            username: Account username (email address), required
            password: Account password (optional, defaults to empty string)
            domain: Domain name (optional, auto-extracted from username if not provided)
            is_active: Whether account is active (optional, defaults to True)
            
        Returns:
            Created account dictionary
            
        Raises:
            ValueError: If username is empty or invalid
            IntegrityError: If account with username already exists
        """
        try:
            username = username.strip()
            if not username:
                raise ValueError("Username is required")

            # Check if username already exists
            existing = get_account_by_username_any(username)
            if existing:
                raise ValueError(f"Account with username '{username}' already exists")

            # Create account
            account = create_account(
                username=username,
                password=password,
                domain=domain,
                is_active=is_active
            )

            return self._account_to_dict(account)

        except ValueError as e:
            logger.warning(f"[MailAccountService.create_account] Validation error: {e}")
            raise
        except Exception as e:
            logger.exception(f"[MailAccountService.create_account] Error creating account: {e}")
            # Check for unique constraint violations
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                raise ValueError(f"Account with username '{username}' already exists")
            raise

    def update_account(
            self,
            account_id: int,
            username: Optional[str] = None,
            password: Optional[str] = None,
            domain: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update mail account
        
        Args:
            account_id: Account ID
            username: New username (optional)
            password: New password (optional)
            domain: New domain (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated account dictionary or None if account not found
            
        Raises:
            ValueError: If username validation fails or username already exists
            IntegrityError: If username constraint violation
        """
        try:
            account = get_account_by_id(account_id)
            if not account:
                return None

            # Prepare update fields
            update_username = username.strip() if username else None

            # If username is being updated, check for conflicts
            if update_username and update_username != account.username:
                existing = get_account_by_username_any(update_username)
                if existing and existing.id != account_id:
                    raise ValueError(f"Account with username '{update_username}' already exists")

            # Update account
            updated_account = update_account(
                account_id=account_id,
                username=update_username,
                password=password,
                domain=domain,
                is_active=is_active
            )

            if not updated_account:
                return None

            return self._account_to_dict(updated_account)

        except ValueError as e:
            logger.warning(f"[MailAccountService.update_account] Validation error: {e}")
            raise
        except Exception as e:
            logger.exception(f"[MailAccountService.update_account] Error updating account: {e}")
            # Check for unique constraint violations
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                if username:
                    raise ValueError(f"Account with username '{username}' already exists")
            raise

    def delete_account(self, account_id: int) -> bool:
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

            # Delete account
            success = delete_account(account_id)
            return success

        except Exception as e:
            logger.exception(f"[MailAccountService.delete_account] Error deleting account: {e}")
            raise

    def _account_to_dict(self, account) -> Dict[str, Any]:
        """
        Convert MailAccount model instance to dictionary
        
        Args:
            account: MailAccount model instance
            
        Returns:
            Account dictionary
        """
        return {
            'id': account.id,
            'username': account.username,
            'domain': account.domain,
            'is_active': account.is_active,
            'ct': account.ct,
            'dt': account.dt,
        }
