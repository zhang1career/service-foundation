"""
Knowledge REST API views: CRUD for knowledge metadata.
Generated.
"""
import json
import logging

from django.db import DatabaseError, IntegrityError
from rest_framework import status as http_status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.services.knowledge_service import KnowledgeService
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
    RET_INVALID_PARAM,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

logger = logging.getLogger(__name__)


def _parse_entity_id(entity_id) -> int:
    """Parse and validate entity_id from URL. Raises ValueError if invalid."""
    try:
        eid = int(entity_id) if entity_id is not None else None
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")
    if eid is None or eid <= 0:
        raise ValueError("entity_id must be a positive integer")
    return eid


class KnowledgeListView(APIView):
    """List and create knowledge entities."""

    def get(self, request, *args, **kwargs):
        """List knowledge with optional offset, limit, source_type."""
        try:
            raw_offset = request.GET.get("offset", 0)
            raw_limit = request.GET.get("limit", 100)
            try:
                offset = int(with_type(raw_offset)) if raw_offset not in (None, "") else 0
                limit = int(with_type(raw_limit)) if raw_limit not in (None, "") else 100
            except (TypeError, ValueError):
                raise ValueError("offset and limit must be integers")
            source_type = (request.GET.get("source_type") or "").strip() or None
            service = KnowledgeService()
            page_data = service.list_knowledge(
                offset=offset,
                limit=limit,
                source_type=source_type,
            )
            return resp_ok(page_data)
        except ValueError as e:
            logger.warning("[KnowledgeListView.get] Validation error: %s", e)
            return resp_err(str(e), code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
        except (DatabaseError, IntegrityError) as e:
            logger.exception("[KnowledgeListView.get] DB error: %s", e)
            return resp_err(str(e), code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeListView.get] Error: %s", e)
            return resp_exception(e)

    def post(self, request, *args, **kwargs):
        """Create a knowledge entity. Body: title (required), description, source_type, metadata."""
        try:
            data = getattr(request, "data", None) or request.POST
            if data is None:
                data = {}
            title = (data.get("title") or "").strip()
            description = data.get("description")
            source_type = data.get("source_type")
            metadata = data.get("metadata")
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata) if metadata else None
            service = KnowledgeService()
            out = service.create_knowledge(
                title=title,
                description=description,
                source_type=source_type,
                metadata=metadata,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeListView.post] Validation error: %s", e)
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
        except (DatabaseError, IntegrityError) as e:
            logger.exception("[KnowledgeListView.post] DB error: %s", e)
            return resp_err(str(e), code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except ParseError as e:
            logger.warning("[KnowledgeListView.post] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeListView.post] Error: %s", e)
            return resp_exception(e)


class KnowledgeDetailView(APIView):
    """Get, update, delete a single knowledge entity by id."""

    def get(self, request, entity_id, *args, **kwargs):
        """Get one knowledge entity by id."""
        try:
            entity_id = _parse_entity_id(entity_id)
            service = KnowledgeService()
            out = service.get_knowledge(entity_id)
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeDetailView.get] Validation error: %s", e)
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except (DatabaseError, IntegrityError) as e:
            logger.exception("[KnowledgeDetailView.get] DB error: %s", e)
            return resp_err(str(e), code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeDetailView.get] Error: %s", e)
            return resp_exception(e)

    def put(self, request, entity_id, *args, **kwargs):
        """Update knowledge entity. Body: title, description, source_type, metadata (all optional)."""
        try:
            entity_id = _parse_entity_id(entity_id)
            data = getattr(request, "data", None) or request.POST or {}
            title = data.get("title")
            description = data.get("description")
            source_type = data.get("source_type")
            metadata = data.get("metadata")
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata) if metadata else None
            service = KnowledgeService()
            out = service.update_knowledge(
                entity_id=entity_id,
                title=title,
                description=description,
                source_type=source_type,
                metadata=metadata,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeDetailView.put] Validation error: %s", e)
            msg = str(e)
            msg_lower = msg.lower()
            if "not found" in msg_lower:
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            if "empty" in msg_lower or "required" in msg_lower:
                return resp_err(msg, code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except (DatabaseError, IntegrityError) as e:
            logger.exception("[KnowledgeDetailView.put] DB error: %s", e)
            return resp_err(str(e), code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except ParseError as e:
            logger.warning("[KnowledgeDetailView.put] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeDetailView.put] Error: %s", e)
            return resp_exception(e)

    def delete(self, request, entity_id, *args, **kwargs):
        """Delete knowledge entity by id."""
        try:
            entity_id = _parse_entity_id(entity_id)
            service = KnowledgeService()
            service.delete_knowledge(entity_id)
            return resp_ok(None)
        except ValueError as e:
            logger.warning("[KnowledgeDetailView.delete] Validation error: %s", e)
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except (DatabaseError, IntegrityError) as e:
            logger.exception("[KnowledgeDetailView.delete] DB error: %s", e)
            return resp_err(str(e), code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeDetailView.delete] Error: %s", e)
            return resp_exception(e)
