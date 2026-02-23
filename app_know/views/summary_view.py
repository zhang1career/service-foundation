"""
REST API views for knowledge summaries: trigger generation, get, list. Generated.
"""
import json
import logging

from rest_framework import status as http_status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.services.summary_service import SummaryService, _validate_app_id
from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_RESOURCE_NOT_FOUND,
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

logger = logging.getLogger(__name__)


def _parse_entity_id(entity_id) -> int:
    """Parse and validate entity_id from URL. Raises ValueError if invalid."""
    if entity_id is None or entity_id == "":
        raise ValueError("entity_id is required")
    if isinstance(entity_id, float) and not entity_id.is_integer():
        raise ValueError("entity_id must be an integer")
    try:
        eid = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")
    if eid is None or eid <= 0:
        raise ValueError("entity_id must be a positive integer")
    return eid


def _error_code_for_validation(msg: str) -> int:
    """Map ValueError message to response error code."""
    m = msg.lower()
    if "not found" in m:
        return RET_RESOURCE_NOT_FOUND
    if "required" in m or "cannot be empty" in m or "missing" in m:
        return RET_MISSING_PARAM
    return RET_INVALID_PARAM


class KnowledgeSummaryView(APIView):
    """GET: retrieve summary. POST: trigger generation. PUT: update. DELETE: delete. Query/Body: app_id."""

    def get(self, request, entity_id, *args, **kwargs):
        """Get summary for knowledge <entity_id>. Optional query param: app_id (int, default 0)."""
        try:
            entity_id = _parse_entity_id(entity_id)
            raw_app_id = request.GET.get("app_id")
            app_id = _validate_app_id(raw_app_id)
            service = SummaryService()
            out = service.get_summary(knowledge_id=entity_id, app_id=app_id)
            if out is None:
                return resp_err(
                    f"Summary for knowledge id {entity_id} not found",
                    code=RET_RESOURCE_NOT_FOUND,
                    status=http_status.HTTP_200_OK,
                )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeSummaryView.get] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("[KnowledgeSummaryView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def post(self, request, entity_id, *args, **kwargs):
        """Generate and persist summary for knowledge <entity_id>. Body: app_id, use_ai (optional)."""
        try:
            entity_id = _parse_entity_id(entity_id)
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}
            raw_app_id = data.get("app_id")
            app_id = _validate_app_id(raw_app_id)
            use_ai = data.get("use_ai", False)
            service = SummaryService()
            out = service.generate_and_save(knowledge_id=entity_id, app_id=app_id, use_ai=use_ai)
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeSummaryView.post] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except ParseError as e:
            logger.warning("[KnowledgeSummaryView.post] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeSummaryView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def put(self, request, entity_id, *args, **kwargs):
        """Update summary for knowledge <entity_id>. Body: app_id (required), summary, source."""
        try:
            entity_id = _parse_entity_id(entity_id)
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    data = {}
            raw_app_id = data.get("app_id")
            app_id = _validate_app_id(raw_app_id)
            summary = data.get("summary")
            source = data.get("source")
            service = SummaryService()
            out = service.update_summary(
                knowledge_id=entity_id,
                app_id=app_id,
                summary=summary,
                source=source,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeSummaryView.put] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except ParseError as e:
            logger.warning("[KnowledgeSummaryView.put] Parse error: %s", e)
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeSummaryView.put] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def delete(self, request, entity_id, *args, **kwargs):
        """Delete summary for knowledge <entity_id>. Query param: app_id (optional, default 0)."""
        try:
            entity_id = _parse_entity_id(entity_id)
            app_id = _validate_app_id(request.GET.get("app_id"))
            service = SummaryService()
            service.delete_summary(knowledge_id=entity_id, app_id=app_id)
            return resp_ok(None)
        except ValueError as e:
            logger.warning("[KnowledgeSummaryView.delete] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("[KnowledgeSummaryView.delete] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)


class KnowledgeSummaryListView(APIView):
    """GET: list summaries with optional filters (app_id, knowledge_id, limit, offset)."""

    def get(self, request, *args, **kwargs):
        """List summaries. Query: app_id, knowledge_id, limit, offset."""
        try:
            raw_app_id = request.GET.get("app_id")
            app_id = _validate_app_id(raw_app_id)  # default 0
            knowledge_id = request.GET.get("knowledge_id")
            if knowledge_id is not None and knowledge_id != "":
                try:
                    knowledge_id = int(with_type(knowledge_id))
                except (TypeError, ValueError):
                    knowledge_id = None
            raw_limit = request.GET.get("limit", 100)
            raw_offset = request.GET.get("offset", 0)
            try:
                limit = int(with_type(raw_limit)) if raw_limit not in (None, "") else 100
                offset = int(with_type(raw_offset)) if raw_offset not in (None, "") else 0
            except (TypeError, ValueError):
                raise ValueError("limit and offset must be integers")
            if limit <= 0 or limit > LIMIT_LIST:
                raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
            if offset < 0:
                raise ValueError("offset must be >= 0")
            service = SummaryService()
            out = service.list_summaries(
                app_id=app_id,
                knowledge_id=knowledge_id,
                offset=offset,
                limit=limit,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[KnowledgeSummaryListView.get] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("[KnowledgeSummaryListView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
