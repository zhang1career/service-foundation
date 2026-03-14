"""
Extract view: trigger Extractor Agent + Graph Builder for a knowledge document.
Phase 2: 摘要抽取 + 主谓宾定状补 -> MySQL + Neo4j.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.repos.knowledge_point_repo import list_by_batch
from app_know.services.extractor_agent import extract_and_store_for_batch
from app_know.services.graph_builder_agent import build_graph_for_knowledge
from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


class KnowledgeExtractView(APIView):
    """POST to extract brief + 主谓宾 from sentences and build Neo4j graph."""

    def post(self, request, entity_id, *args, **kwargs):
        """
        Extract for all sentences: AI extracts 摘要+主谓宾, updates MySQL, builds Neo4j graph.
        Body: use_ai (optional, default true).
        """
        try:
            if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
                return resp_err("entity_id must be a positive integer", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            # entity_id = batch_id
            items, _ = list_by_batch(entity_id, limit=1)
            if not items:
                return resp_err(
                    f"Batch {entity_id} has no knowledge points (parse first)",
                    code=RET_RESOURCE_NOT_FOUND,
                    status=http_status.HTTP_200_OK,
                )

            data = getattr(request, "data", None) or {}
            use_ai = data.get("use_ai", True)

            results = extract_and_store_for_batch(batch_id=entity_id, use_ai=use_ai)
            ok_count = sum(1 for r in results if r.get("ok"))
            graph_result = build_graph_for_knowledge(kid=entity_id)

            return resp_ok({
                "kid": entity_id,
                "extracted_count": ok_count,
                "total_count": len(results),
                "graph": {
                    "created_nodes": graph_result.get("created_nodes", 0),
                    "created_edges": graph_result.get("created_edges", 0),
                    "skipped": graph_result.get("skipped", 0),
                    "errors": graph_result.get("errors", []),
                },
                "results": [
                    {
                        "sentence_id": r.get("sentence_id"),
                        "ok": r.get("ok"),
                        "brief": r.get("brief"),
                        "graph_subject": r.get("graph_subject"),
                        "graph_object": r.get("graph_object"),
                        "error": r.get("error"),
                    }
                    for r in results
                ],
            })
        except ValueError as e:
            logger.warning("[KnowledgeExtractView] Validation error: %s", e)
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeExtractView] Error: %s", e)
            return resp_exception(e)


class SentenceGraphView(APIView):
    """GET sentence-level SVO graph for a knowledge document."""

    def get(self, request, entity_id, *args, **kwargs):
        """Return Neo4j sentence graph (nodes, edges) for vis-network."""
        try:
            if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
                return resp_err("entity_id must be a positive integer", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            items, _ = list_by_batch(entity_id, limit=1)
            if not items:
                return resp_err(
                    f"Batch {entity_id} has no knowledge points",
                    code=RET_RESOURCE_NOT_FOUND,
                    status=http_status.HTTP_200_OK,
                )

            from app_know.services.graph_builder_agent import get_sentence_graph
            graph_data = get_sentence_graph(kid=entity_id)  # kid = batch_id for Neo4j
            return resp_ok(graph_data)
        except ValueError as e:
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[SentenceGraphView] Error: %s", e)
            return resp_exception(e)
