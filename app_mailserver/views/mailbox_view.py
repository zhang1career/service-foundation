"""
Mailbox REST API views

This module provides CRUD operations for mailboxes.
Views are responsible for HTTP request/response handling only.
Business logic is handled by MailboxService.
"""
import logging
from rest_framework import status as http_status
from rest_framework.views import APIView

from app_mailserver.services.mailbox_service import MailboxService
from common.consts.query_const import LIMIT_PAGE
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_RESOURCE_EXISTS,
    RET_DB_ERROR,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

logger = logging.getLogger(__name__)


class MailboxListView(APIView):
    """List and create mailboxes for an account"""

    def get(self, request, account_id, *args, **kwargs):
        """
        List mailboxes for an account with pagination
        
        URL parameter:
        - account_id: Account ID
        
        Query parameters:
        - offset: Pagination offset (default: 0)
        - limit: Pagination limit (default: 1000, max: 1000)
        """
        try:
            account_id = with_type(account_id)
            
            # Get query parameters
            offset = with_type(request.GET.get("offset", 0))
            limit = with_type(request.GET.get("limit", 1000))
            
            # Call service to list mailboxes
            service = MailboxService()
            page_data = service.list_mailboxes(
                account_id=account_id,
                offset=offset,
                limit=limit
            )
            
            return resp_ok(page_data)
            
        except ValueError as e:
            logger.warning(f"[MailboxListView.get] Validation error: {e}")
            error_message = str(e)
            if 'not found' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(error_message, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"[MailboxListView.get] Error listing mailboxes: {e}")
            return resp_exception(e)

    def post(self, request, account_id, *args, **kwargs):
        """
        Create a new mailbox for an account
        
        URL parameter:
        - account_id: Account ID
        
        Request body (JSON):
        {
            "name": "INBOX",              # Required
            "path": "INBOX",              # Required
            "message_count": 0,           # Optional, defaults to 0
            "unread_count": 0             # Optional, defaults to 0
        }
        """
        try:
            account_id = with_type(account_id)
            
            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST
            
            name = (data.get('name') or '').strip()
            path = (data.get('path') or '').strip()
            message_count = with_type(data.get('message_count', 0))
            unread_count = with_type(data.get('unread_count', 0))
            
            # Call service to create mailbox
            service = MailboxService()
            mailbox_data = service.create_mailbox(
                account_id=account_id,
                name=name,
                path=path,
                message_count=message_count,
                unread_count=unread_count
            )
            
            return resp_ok(mailbox_data)
            
        except ValueError as e:
            logger.warning(f"[MailboxListView.post] Validation error: {e}")
            error_message = str(e)
            if 'required' in error_message.lower() or 'cannot be empty' in error_message.lower():
                return resp_err(error_message, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            elif 'already exists' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_EXISTS, status=http_status.HTTP_200_OK)
            elif 'not found' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(error_message, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"[MailboxListView.post] Error creating mailbox: {e}")
            return resp_exception(e)


class MailboxDetailView(APIView):
    """Get, update, and delete a specific mailbox"""

    def get(self, request, mailbox_id, *args, **kwargs):
        """
        Get mailbox by ID
        
        URL parameter:
        - mailbox_id: Mailbox ID
        """
        try:
            mailbox_id = with_type(mailbox_id)
            
            # Call service to get mailbox
            service = MailboxService()
            mailbox_data = service.get_mailbox(mailbox_id)
            
            if not mailbox_data:
                return resp_err("Mailbox not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)
            
            return resp_ok(mailbox_data)
            
        except Exception as e:
            logger.exception(f"[MailboxDetailView.get] Error getting mailbox: {e}")
            return resp_exception(e)

    def put(self, request, mailbox_id, *args, **kwargs):
        """
        Update mailbox
        
        URL parameter:
        - mailbox_id: Mailbox ID
        
        Request body (JSON):
        {
            "name": "NewName",            # Optional
            "path": "NewPath",            # Optional
            "message_count": 10,          # Optional
            "unread_count": 5             # Optional
        }
        """
        try:
            mailbox_id = with_type(mailbox_id)
            
            # Get request data
            data = request.data if hasattr(request, 'data') else request.POST
            
            # Prepare update fields
            name = data.get('name', '').strip() if 'name' in data else None
            path = data.get('path', '').strip() if 'path' in data else None
            message_count = with_type(data.get('message_count')) if 'message_count' in data else None
            unread_count = with_type(data.get('unread_count')) if 'unread_count' in data else None
            
            # Call service to update mailbox
            service = MailboxService()
            mailbox_data = service.update_mailbox(
                mailbox_id=mailbox_id,
                name=name,
                path=path,
                message_count=message_count,
                unread_count=unread_count
            )
            
            if not mailbox_data:
                return resp_err("Mailbox not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)
            
            return resp_ok(mailbox_data)
            
        except ValueError as e:
            logger.warning(f"[MailboxDetailView.put] Validation error: {e}")
            error_message = str(e)
            if 'cannot be empty' in error_message.lower() or 'cannot be negative' in error_message.lower():
                return resp_err(error_message, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            elif 'already exists' in error_message.lower():
                return resp_err(error_message, code=RET_RESOURCE_EXISTS, status=http_status.HTTP_200_OK)
            return resp_err(error_message, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"[MailboxDetailView.put] Error updating mailbox: {e}")
            return resp_exception(e)

    def patch(self, request, mailbox_id, *args, **kwargs):
        """
        Partially update mailbox (same as PUT)
        """
        return self.put(request, mailbox_id, *args, **kwargs)

    def delete(self, request, mailbox_id, *args, **kwargs):
        """
        Delete mailbox (hard delete)
        
        URL parameter:
        - mailbox_id: Mailbox ID
        """
        try:
            mailbox_id = with_type(mailbox_id)
            
            # Call service to delete mailbox
            service = MailboxService()
            success = service.delete_mailbox(mailbox_id)
            
            if not success:
                return resp_err("Mailbox not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)
            
            return resp_ok({"message": "Mailbox deleted successfully"})
            
        except Exception as e:
            logger.exception(f"[MailboxDetailView.delete] Error deleting mailbox: {e}")
            return resp_exception(e)

