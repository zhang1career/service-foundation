"""
REST API view for logical query: natural-language or keyword query -> Atlas + Neo4j -> ranked results.
Generated.
"""
import json
import logging

from rest_framework import status as http_status
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.repos.summary_repo import QUERY_SEARCH_MAX_LEN
from app_know.services.query_service import LogicalQueryService
from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
)
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)

DEFAULT_QUERY_LIMIT = 50


def _error_code_for_validation(msg: str) -> int:
    if "required" in msg.lower() or "cannot be empty" in msg.lower():
        return RET_MISSING_PARAM
    return RET_INVALID_PARAM


class LogicalQueryView(APIView):
    """
    POST/GET: logical query. Accepts natural-language or keyword query;
    returns combined ranked results from Atlas (summary relevance) and Neo4j (graph reasoning).
    Query param or body: query (or q), app_id (optional), limit (optional).
    """

    def _get_params(self, request):
        """Extract query, app_id, limit from GET query params or POST body."""
        if request.method == "GET":
            query = (request.GET.get("query") or request.GET.get("q") or "").strip()
            app_id = (request.GET.get("app_id") or "").strip() or None
            raw_limit = request.GET.get("limit")
        else:
            data = getattr(request, "data", None) or request.POST or {}
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except json.JSONDecodeError:
                    raise ParseError("Invalid JSON body")
            if not isinstance(data, dict):
                data = {}
            if not data:
                raw = getattr(request, "body", None)
                if raw:
                    ct = (getattr(request, "content_type", "") or "").split(";")[0].strip().lower()
                    if ct == "application/json":
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", errors="replace")
                        if isinstance(raw, str) and raw.strip():
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                raise ParseError("Invalid JSON body")
            if not isinstance(data, dict):
                data = {}
            query = (data.get("query") or data.get("q") or "").strip()
            app_id = (data.get("app_id") or "").strip() or None
            raw_limit = data.get("limit")
        if query and len(query) > QUERY_SEARCH_MAX_LEN:
            raise ValueError(f"query must not exceed {QUERY_SEARCH_MAX_LEN} characters")
        limit = DEFAULT_QUERY_LIMIT
        if raw_limit is not None and raw_limit != "":
            try:
                limit = int(raw_limit)
            except (TypeError, ValueError):
                raise ValueError("limit must be an integer")
            if limit <= 0 or limit > LIMIT_LIST:
                raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
        return query, app_id, limit

    def get(self, request, *args, **kwargs):
        """GET: logical query. Query params: query or q (required), app_id, limit."""
        try:
            query, app_id, limit = self._get_params(request)
            if not query:
                return resp_err(
                    "query is required (use query= or q=)",
                    code=RET_MISSING_PARAM,
                    status=http_status.HTTP_200_OK,
                )
            service = LogicalQueryService()
            out = service.query(query=query, app_id=app_id, limit=limit)
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[LogicalQueryView.get] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except ParseError as e:
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[LogicalQueryView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """POST: logical query. Body: query or q (required), app_id, limit."""
        try:
            query, app_id, limit = self._get_params(request)
            if not query:
                return resp_err(
                    "query is required (use query or q in body)",
                    code=RET_MISSING_PARAM,
                    status=http_status.HTTP_200_OK,
                )
            service = LogicalQueryService()
            out = service.query(query=query, app_id=app_id, limit=limit)
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[LogicalQueryView.post] Validation error: %s", e)
            return resp_err(
                str(e),
                code=_error_code_for_validation(str(e)),
                status=http_status.HTTP_200_OK,
            )
        except ParseError as e:
            return resp_err(str(e), code=RET_JSON_PARSE_ERROR, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[LogicalQueryView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR, status=http_status.HTTP_200_OK)
