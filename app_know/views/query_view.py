"""
REST API view for Graphiti-based logical query.
"""
import json
import logging

from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from app_know.services.query_service import LogicalQueryService, QUERY_SEARCH_MAX_LEN
from common.consts.query_const import LIMIT_LIST
from common.consts.response_const import (
    RET_MISSING_PARAM,
    RET_INVALID_PARAM,
    RET_DB_ERROR,
    RET_JSON_PARSE_ERROR,
)
from common.exceptions.base_exception import generic_code_for_ret
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)

DEFAULT_QUERY_LIMIT = 50
class LogicalQueryView(APIView):
    """
    POST/GET: logical query. Accepts natural-language or keyword query and
    returns Graphiti semantic retrieval results.

    Query params / body:
        - query or q (required): Search query string
        - app_id (optional): Application ID for scoping
        - limit (optional): Maximum number of results (default: 50)
        - format (optional): Output format - "list" (default) or "triple" for predicate logic
    """

    def _get_params(self, request):
        """Extract query parameters from GET query params or POST body."""
        if request.method == "GET":
            query = (request.GET.get("query") or request.GET.get("q") or "").strip()
            app_id = (request.GET.get("app_id") or "").strip() or None
            raw_limit = request.GET.get("limit")
            output_format = (request.GET.get("format") or "").strip().lower() or "list"
        else:
            data = getattr(request, "data", None)
            if data is not None:
                if not isinstance(data, dict):
                    data = {}
            else:
                data = request.POST or {}
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
            output_format = (data.get("format") or "").strip().lower() or "list"

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

        if output_format not in ("list", "triple"):
            output_format = "list"

        return query, app_id, limit, output_format

    def get(self, request, *args, **kwargs):
        """GET: Graphiti logical query endpoint."""
        try:
            query, app_id, limit, output_format = self._get_params(request)
            if not query:
                return resp_err(code=RET_MISSING_PARAM, message="query is required (use query= or q=)")
            service = LogicalQueryService()
            out = service.query(
                query=query,
                app_id=app_id,
                limit=limit,
                output_format=output_format,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[LogicalQueryView.get] Validation error: %s", e)
            return resp_err(code=generic_code_for_ret(str(e), RET_INVALID_PARAM)[0], message=str(e))
        except ParseError as e:
            return resp_err(code=RET_JSON_PARSE_ERROR, message=str(e))
        except Exception as e:
            logger.exception("[LogicalQueryView.get] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR)

    def post(self, request, *args, **kwargs):
        """POST: Graphiti logical query endpoint."""
        try:
            query, app_id, limit, output_format = self._get_params(request)
            if not query:
                return resp_err(code=RET_MISSING_PARAM, message="query is required (use query or q in body)")
            service = LogicalQueryService()
            out = service.query(
                query=query,
                app_id=app_id,
                limit=limit,
                output_format=output_format,
            )
            return resp_ok(out)
        except ValueError as e:
            logger.warning("[LogicalQueryView.post] Validation error: %s", e)
            return resp_err(code=generic_code_for_ret(str(e), RET_INVALID_PARAM)[0], message=str(e))
        except ParseError as e:
            return resp_err(code=RET_JSON_PARSE_ERROR, message=str(e))
        except Exception as e:
            logger.exception("[LogicalQueryView.post] Error: %s", e)
            return resp_exception(e, code=RET_DB_ERROR)
