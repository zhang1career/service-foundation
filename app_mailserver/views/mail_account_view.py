"""
Mail account REST API views

This module provides CRUD operations for mail accounts.
Views are responsible for HTTP request/response handling only.
Business logic is handled by MailAccountService.
"""
import logging
from rest_framework import status as http_status
from rest_framework.views import APIView

from app_mailserver.services.mail_account_service import MailAccountService
from common.consts.query_const import LIMIT_PAGE
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_RESOURCE_EXISTS,
    RET_DB_ERROR,
)
from common.consts.string_const import EMPTY_STRING
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

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
        - username: Search keyword for username (optional)
        """
        try:
            # Get query parameters
            offset = with_type(request.GET.get("offset", 0))
            limit = with_type(request.GET.get("limit", LIMIT_PAGE))
            domain = request.GET.get("domain", EMPTY_STRING)
            is_active_str = request.GET.get("is_active", EMPTY_STRING)
            username = request.GET.get("username", EMPTY_STRING)

            # Parse is_active
            is_active = None
            if is_active_str:
                is_active = with_type(is_active_str)

            # Call service to list accounts
            service = MailAccountService()
            page_data = service.list_accounts(
                offset=offset,
                limit=limit,
                domain=domain,
                is_active=is_active,
                username=username
            )

            return resp_ok(page_data)

        except Exception as e:
            logger.exception(f"[MailAccountListView.get] Error listing accounts: {e}")
            return resp_exception(e)

    def post(self, request, *args, **kwargs):
        """
        Create a new mail account
        
        Request body (JSON):
        {
            "username": "user@example.com",   # Required
            "password": "password123",        # Optional, defaults to empty string
            "domain": "example.com",          # Optional, auto-extracted from username if not provided
            "is_active": true                 # Optional, defaults to true
        }
        """
        try:
            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST

            username = (data.get('username') or '').strip()
            password = data.get('password', '')
            domain = data.get('domain', 'localhost')
            is_active = with_type(data.get('is_active', True))

            # Call service to create account
            service = MailAccountService()
            account_data = service.create_account(
                username=username,
                password=password,
                domain=domain,
                is_active=is_active
            )

            return resp_ok(account_data)

        except ValueError as e:
            logger.warning(f"[MailAccountListView.post] Validation error: {e}")
            error_message = str(e)
            if 'required' in error_message.lower():
                return resp_err(error_message, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            elif 'already exists' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_EXISTS, status=http_status.HTTP_200_OK)
            return resp_err(error_message, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"[MailAccountListView.post] Error creating account: {e}")
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

            # Call service to get account
            service = MailAccountService()
            account_data = service.get_account(account_id)

            if not account_data:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

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

            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST

            # Prepare update fields
            username = data.get('username', '').strip() if 'username' in data else None
            password = data.get('password') if 'password' in data else None
            domain = data.get('domain') if 'domain' in data else None
            is_active = with_type(data.get('is_active')) if 'is_active' in data else None

            # Call service to update account
            service = MailAccountService()
            account_data = service.update_account(
                account_id=account_id,
                username=username,
                password=password,
                domain=domain,
                is_active=is_active
            )

            if not account_data:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            return resp_ok(account_data)

        except ValueError as e:
            logger.warning(f"[MailAccountDetailView.put] Validation error: {e}")
            error_message = str(e)
            if 'already exists' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_EXISTS, status=http_status.HTTP_200_OK)
            return resp_err(error_message, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"[MailAccountDetailView.put] Error updating account: {e}")
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

            # Call service to delete account
            service = MailAccountService()
            success = service.delete_account(account_id)

            if not success:
                return resp_err("Account not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            return resp_ok({"message": "Account deleted successfully"})

        except Exception as e:
            logger.exception(f"[MailAccountDetailView.delete] Error deleting account: {e}")
            return resp_exception(e)
