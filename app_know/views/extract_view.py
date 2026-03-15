"""
Extract view: trigger Extractor Agent + Graph Builder for a knowledge document.
Phase 2: 摘要抽取 + 主谓宾定状补 -> MySQL + Neo4j.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.repos.knowledge_point_repo import list_by_batch, get_by_id, update as update_knowledge_point
from app_know.services.extractor_agent import extract_and_store_for_batch, extract_sentence, extract_brief_with_options
from app_know.services.graph_builder_agent import (
    build_graph_for_knowledge,
    get_top_noun_nodes,
    get_top_predicate_edges,
)
from app_know.enums.stage_enum import StageEnum
from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
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


class ExtractBriefView(APIView):
    """POST to extract brief for a single knowledge point; writes brief and sets stage=1 (已清洗)."""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err("point_id must be a positive integer", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            point = get_by_id(point_id)
            if not point:
                return resp_err(
                    f"Knowledge point {point_id} not found",
                    code=RET_RESOURCE_NOT_FOUND,
                    status=http_status.HTTP_200_OK,
                )
            content = (point.content or "").strip()
            if not content:
                return resp_err("Point content is empty", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            subject_list = get_top_noun_nodes(100)
            predicate_list = get_top_predicate_edges(100)
            extracted = extract_brief_with_options(content, subject_list, predicate_list)
            if not extracted:
                return resp_err(
                    "Extract failed or AI unavailable",
                    code=RET_INVALID_PARAM,
                    status=http_status.HTTP_200_OK,
                )
            brief = (extracted.get("brief") or "").strip() or content[:100]
            sub_idx = extracted.get("sub_idx", -1)
            prd_idx = extracted.get("prd_idx", -1)
            if sub_idx < 0 or prd_idx < 0:
                new_status = KnowledgeStatusEnum.PENDING_REVIEW
            else:
                new_status = KnowledgeStatusEnum.COMPLETED
            ok = update_knowledge_point(
                point_id, brief=brief, stage=StageEnum.CLEANED, status=new_status
            )
            if not ok:
                return resp_err("Update failed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            return resp_ok({
                "brief": brief,
                "stage": StageEnum.CLEANED,
                "status": new_status,
                "sub_idx": sub_idx,
                "prd_idx": prd_idx,
            })
        except Exception as e:
            logger.exception("[ExtractBriefView] Error: %s", e)
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
