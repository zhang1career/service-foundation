"""
Graphiti ingestion/query views for knowledge workflow.
"""
import logging

from rest_framework.views import APIView

from app_know.repos.knowledge_point_repo import get_by_id, list_by_batch
from app_know.services.graphiti_knowledge_service import GraphitiKnowledgeService
from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


class KnowledgeExtractView(APIView):
    """POST: ingest all points in batch to Graphiti."""

    def post(self, request, entity_id, *args, **kwargs):
        try:
            if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
                return resp_err(code=RET_INVALID_PARAM, message="entity_id must be a positive integer")
            items, _ = list_by_batch(entity_id, limit=1)
            if not items:
                return resp_err(
                    code=RET_RESOURCE_NOT_FOUND,
                    message=f"Batch {entity_id} has no knowledge points (parse first)",
                )
            result = GraphitiKnowledgeService().ingest_batch(entity_id)
            return resp_ok(result)
        except ValueError as e:
            logger.warning("[KnowledgeExtractView] Validation error: %s", e)
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[KnowledgeExtractView] Error: %s", e)
            return resp_exception(e)


class ExtractBriefView(APIView):
    """POST: ingest single point to Graphiti and refresh brief."""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err(code=RET_INVALID_PARAM, message="point_id must be a positive integer")
            point = get_by_id(point_id)
            if not point:
                return resp_err(code=RET_RESOURCE_NOT_FOUND, message=f"Knowledge point {point_id} not found")
            result = GraphitiKnowledgeService().ingest_point(point_id=point_id)
            return resp_ok(result)
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[ExtractBriefView] Error: %s", e)
            return resp_exception(e)


class MemoryGraphView(APIView):
    """POST: get point-related memory graph from Graphiti."""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err(code=RET_INVALID_PARAM, message="point_id required")
            point = get_by_id(point_id)
            if not point:
                return resp_err(code=RET_RESOURCE_NOT_FOUND, message="Knowledge point not found")
            query = (getattr(request, "data", None) or {}).get("query")
            if not isinstance(query, str) or not query.strip():
                query = (point.brief or point.content or "").strip()
            if not query:
                return resp_err(code=RET_INVALID_PARAM, message="query is empty")
            batch_id = int(point.batch_id or 0)
            graph = GraphitiKnowledgeService().memory_graph(query=query, batch_id=batch_id, limit=20)
            return resp_ok({"nodes": graph.get("nodes", []), "edges": graph.get("edges", [])})
        except ValueError as e:
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[MemoryGraphView] Error: %s", e)
            return resp_exception(e)
