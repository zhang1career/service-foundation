"""
Mail account REST API views

This module provides CRUD operations for mail accounts.
"""
import logging
from rest_framework import status as http_status
from rest_framework.views import APIView

from app_mailserver.repos import (
    get_account_by_id,
    list_accounts,
    create_account,
    update_account,
    delete_account,
)
from common.consts.query_const import LIMIT_PAGE, LIMIT_LIST
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_RESOURCE_EXISTS,
    RET_DB_ERROR,
)
from common.consts.string_const import EMPTY_STRING
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type
from common.utils.page_util import build_page

logger = logging.getLogger(__name__)


class MailAccountListView(APIView):
    """List and create mail accounts"""

    def get(self, request, *args, **kwargs):
        """
        List mail accounts with pagination and filtering
        
        Query parameters:
        - offset: Pagination offset (default: 0)
        - limit: Pagination limit (default: 20, max: 1000)
        - domain: Filter by domain (optional)
        - is_active: Filter by active status (optional, true/false)
        - search: Search keyword for username (optional)
        """
        try:
            # Get query parameters
            offset = with_type(request.GET.get("offset", 0))
            limit = with_type(request.GET.get("limit", LIMIT_PAGE))
            domain = request.GET.get("domain", EMPTY_STRING)
            is_active_str = request.GET.get("is_active", EMPTY_STRING)
            search = request.GET.get("search", EMPTY_STRING)

            # Validate and adjust limit
            if limit <= 0:
                limit = LIMIT_PAGE
            if limit > LIMIT_LIST:
                limit = LIMIT_LIST

            # Parse is_active
            is_active = None
            if is_active_str:
                is_active = with_type(is_active_str)

            # Convert empty strings to None
            domain = domain if domain != EMPTY_STRING else None
            search = search if search != EMPTY_STRING else None

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
                accounts_data.append({
                    'id': account.id,
                    'username': account.username,
                    'domain': account.domain,
                    'is_active': account.is_active,
                    'ct': account.ct,
                    'dt': account.dt,
                })

            # Build paginated response
            next_offset = offset + limit if offset + limit < result['total'] else None
            page_data = build_page(accounts_data, next_offset, result['total'])

            return resp_ok(page_data)

        except Exception as e:
            logger.exception(f"[MailAccountListView.get] Error listing accounts: {e}")
            return resp_exception(e)

    def post(self, request, *args, **kwargs):
        """
        Create a new mail account
        
        Request body (JSON):
        {
            "username": "user@example.com",  # Required
            "password": "password123",        # Optional, defaults to empty string
            "domain": "example.com",          # Optional, auto-extracted from username if not provided
            "is_active": true                 # Optional, defaults to true
        }
        """
        try:
            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST

            username = data.get('username', '').strip()
            if not username:
                return resp_err("Username is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)

            password = data.get('password', '')
            domain = data.get('domain', 'localhost')
            is_active = with_type(data.get('is_active', True))

            # Create account
            account = create_account(
                username=username,
                password=password,
                domain=domain,
                is_active=is_active
            )

            # Return created account
            account_data = {
                'id': account.id,
                'username': account.username,
                'domain': account.domain,
                'is_active': account.is_active,
                'ct': account.ct,
                'dt': account.dt,
            }

            return resp_ok(account_data)

        except Exception as e:
            logger.exception(f"[MailAccountListView.post] Error creating account: {e}")
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                return resp_err("Account with this username already exists", code=RET_RESOURCE_EXISTS,
                                status=http_status.HTTP_200_OK)
            return resp_exception(e)


class MailAccountDetailView(APIView):
    """Get, update, and delete a specific mail account"""

    def get(self, request, account_id, *args, **kwargs):
        """
        Get mail account by ID
        
        URL parameter:
        - account_id: Account ID
        """
        try:
            account_id = with_type(account_id)
            account = get_account_by_id(account_id)

            if not account:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            account_data = {
                'id': account.id,
                'username': account.username,
                'domain': account.domain,
                'is_active': account.is_active,
                'ct': account.ct,
                'dt': account.dt,
            }

            return resp_ok(account_data)

        except Exception as e:
            logger.exception(f"[MailAccountDetailView.get] Error getting account: {e}")
            return resp_exception(e)

    def put(self, request, account_id, *args, **kwargs):
        """
        Update mail account
        
        URL parameter:
        - account_id: Account ID
        
        Request body (JSON):
        {
            "username": "newuser@example.com",  # Optional
            "password": "newpassword",           # Optional
            "domain": "newexample.com",          # Optional
            "is_active": false                   # Optional
        }
        """
        try:
            account_id = with_type(account_id)
            account = get_account_by_id(account_id)

            if not account:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST

            # Prepare update fields
            username = data.get('username', '').strip() if 'username' in data else None
            password = data.get('password') if 'password' in data else None
            domain = data.get('domain') if 'domain' in data else None
            is_active = with_type(data.get('is_active')) if 'is_active' in data else None

            # Update account
            updated_account = update_account(
                account_id=account_id,
                username=username if username else None,
                password=password,
                domain=domain,
                is_active=is_active
            )

            if not updated_account:
                return resp_err("Failed to update account", code=RET_DB_ERROR,
                                status=http_status.HTTP_200_OK)

            # Return updated account
            account_data = {
                'id': updated_account.id,
                'username': updated_account.username,
                'domain': updated_account.domain,
                'is_active': updated_account.is_active,
                'ct': updated_account.ct,
                'dt': updated_account.dt,
            }

            return resp_ok(account_data)

        except Exception as e:
            logger.exception(f"[MailAccountDetailView.put] Error updating account: {e}")
            if 'UNIQUE constraint' in str(e) or 'duplicate key' in str(e).lower():
                return resp_err("Account with this username already exists", code=RET_RESOURCE_EXISTS,
                                status=http_status.HTTP_200_OK)
            return resp_exception(e)

    def patch(self, request, account_id, *args, **kwargs):
        """
        Partially update mail account (same as PUT)
        """
        return self.put(request, account_id, *args, **kwargs)

    def delete(self, request, account_id, *args, **kwargs):
        """
        Delete mail account (hard delete)
        
        URL parameter:
        - account_id: Account ID
        """
        try:
            account_id = with_type(account_id)
            account = get_account_by_id(account_id)

            if not account:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            # Delete account
            success = delete_account(account_id)

            if not success:
                return resp_err("Failed to delete account", code=RET_DB_ERROR,
                                status=http_status.HTTP_200_OK)

            return resp_ok({"message": "Account deleted successfully"})

        except Exception as e:
            logger.exception(f"[MailAccountDetailView.delete] Error deleting account: {e}")
            return resp_exception(e)
