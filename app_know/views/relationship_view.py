"""
REST API views for knowledge relationships (create/update/query).
Generated.
"""
import json
import logging

from rest_framework import status as http_status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.services.relationship_service import RelationshipService
from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_RESOURCE_NOT_FOUND,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _error_code_for_validation(msg: str) -> int:
    """Map ValueError message to response error code. Generated."""
    m = msg.lower()
    if "not found" in m or "app_id mismatch" in m:
        return RET_RESOURCE_NOT_FOUND
    if "required" in m or "cannot be empty" in m or "missing" in m or "non-empty" in m:
        return RET_MISSING_PARAM
    return RET_INVALID_PARAM


def _parse_relationship_id(relationship_id) -> int:
    """Parse and validate relationship_id from URL. Raises ValueError if invalid."""
    if relationship_id is None or relationship_id == "":
        raise ValueError("relationship_id is required")
    if isinstance(relationship_id, bool):
        raise ValueError("relationship_id must be a positive integer")
    try:
        rid = int(relationship_id)
    except (TypeError, ValueError):
        raise ValueError("relationship_id must be a positive integer")
    if rid <= 0:
        raise ValueError("relationship_id must be a positive integer")
    return rid


def _get_body(request):
    """Get request body as dict; parse JSON from request.body when data not already parsed."""
    body = getattr(request, "data", None)
    if body is not None and isinstance(body, dict):
        return body
    post = getattr(request, "POST", None) or {}
    if post:
        return post
    raw = getattr(request, "body", None)
    if raw:
        ct = (getattr(request, "content_type", "") or "").split(";")[0].strip().lower()
        if ct == "application/json":
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            if isinstance(raw, str) and raw.strip():
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    raise ParseError("Invalid JSON body")
    return {}


class RelationshipListView(APIView):
    """Create relationship (POST) and query relationships (GET)."""

    def get(self, request, *args, **kwargs):
        """Query relationships. Query params: app_id (required), knowledge_id, entity_type, entity_id, relationship_type, limit, offset."""
        try:
            app_id = (request.GET.get("app_id") or "").strip()
            if not app_id:
                raise ValueError("app_id is required and cannot be empty")
            knowledge_id = request.GET.get("knowledge_id")
            entity_type = request.GET.get("entity_type")
            entity_id = request.GET.get("entity_id")
            relationship_type = request.GET.get("relationship_type")
            raw_limit = request.GET.get("limit", 100)
            raw_offset = request.GET.get("offset", 0)
            try:
                limit = int(raw_limit) if raw_limit not in (None, "") else 100
                offset = int(raw_offset) if raw_offset not in (None, "") else 0
            except (TypeError, ValueError):
                raise ValueError("limit and offset must be integers")
            if limit <= 0 or limit > LIMIT_LIST:
                raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
            if offset < 0:
                raise ValueError("offset must be >= 0")
            service = RelationshipService()
            out = service.query_relationships(
                app_id=app_id,
                knowledge_id=knowledge_id,
                entity_type=entity_type,
                entity_id=entity_id,
                relationship_type=relationship_type,
                limit=limit,
                offset=offset,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[RelationshipListView.get] Validation error: %s", e)
            msg = str(e)
            return resp_err(msg, code=_error_code_for_validation(msg), status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationshipListView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Create a relationship. Body: app_id, relationship_type, source_knowledge_id; for knowledge_entity: entity_type, entity_id; for knowledge_knowledge: target_knowledge_id; optional properties."""
        try:
            try:
                data = _get_body(request) or {}
            except ParseError:
                raise
            if not isinstance(data, dict):
                data = {}
            app_id = (data.get("app_id") or "").strip()
            relationship_type = (data.get("relationship_type") or "").strip()
            source_knowledge_id = data.get("source_knowledge_id")
            target_knowledge_id = data.get("target_knowledge_id")
            entity_type = data.get("entity_type")
            entity_id = data.get("entity_id")
            properties = data.get("properties")
            if isinstance(properties, dict):
                pass
            else:
                properties = None
            service = RelationshipService()
            out = service.create_relationship(
                app_id=app_id,
                relationship_type=relationship_type,
                source_knowledge_id=source_knowledge_id,
                target_knowledge_id=target_knowledge_id,
                entity_type=entity_type,
                entity_id=entity_id,
                properties=properties,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[RelationshipListView.post] Validation error: %s", e)
            msg = str(e)
            return resp_err(msg, code=_error_code_for_validation(msg), status=http_status.HTTP_200_OK)
        except ParseError as e:
            logger.warning("[RelationshipListView.post] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationshipListView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class RelationshipDetailView(APIView):
    """Get (GET) and update (PUT) a single relationship by id."""

    def get(self, request, relationship_id, *args, **kwargs):
        """Get one relationship by Neo4j relationship id. Query param: app_id (required)."""
        try:
            app_id = (request.GET.get("app_id") or "").strip()
            if not app_id:
                raise ValueError("app_id is required and cannot be empty")
            rid = _parse_relationship_id(relationship_id)
            service = RelationshipService()
            out = service.get_relationship(app_id=app_id, relationship_id=rid)
            if out is None:
                return resp_err(
                    f"Relationship {rid} not found or app_id mismatch",
                    code=RET_RESOURCE_NOT_FOUND,
                    status=http_status.HTTP_200_OK,
                )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[RelationshipDetailView.get] Validation error: %s", e)
            return resp_err(str(e), code=_error_code_for_validation(str(e)), status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationshipDetailView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def put(self, request, relationship_id, *args, **kwargs):
        """Update relationship properties. Body: app_id (required), properties (dict)."""
        try:
            try:
                data = _get_body(request) or {}
            except ParseError:
                raise
            if not isinstance(data, dict):
                data = {}
            app_id = (data.get("app_id") or "").strip()
            if not app_id:
                raise ValueError("app_id is required and cannot be empty")
            properties = data.get("properties")
            if not isinstance(properties, dict):
                raise ValueError("properties must be a non-empty dict")
            if not properties:
                raise ValueError("properties must be a non-empty dict")
            rid = _parse_relationship_id(relationship_id)
            service = RelationshipService()
            out = service.update_relationship(
                app_id=app_id,
                relationship_id=rid,
                properties=properties,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[RelationshipDetailView.put] Validation error: %s", e)
            msg = str(e)
            return resp_err(msg, code=_error_code_for_validation(msg), status=http_status.HTTP_200_OK)
        except ParseError as e:
            logger.warning("[RelationshipDetailView.put] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[RelationshipDetailView.put] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
