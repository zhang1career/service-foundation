"""
Extract view: trigger Extractor Agent + Graph Builder for a knowledge document.
Phase 2: 摘要抽取 + 主谓宾定状补 -> MySQL + Neo4j.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
from app_know.enums.stage_enum import StageEnum
from app_know.repos.deco_repo import upsert_sub_deco, upsert_obj_deco
from app_know.repos.knowledge_point_repo import list_by_batch, get_by_id, update as update_knowledge_point
from app_know.services.extractor_agent import (
    extract_and_store_for_batch,
    extract_brief_with_options,
    analyze_components as do_analyze_components,
)
from app_know.services.graph_builder_agent import (
    build_components_query_cypher,
    build_graph_for_knowledge,
    build_graph_expressions,
    graph_string_to_hash,
    get_top_noun_nodes,
    get_top_predicate_edges,
    save_components as do_save_components,
    run_cypher_to_graph,
)
from app_know.services.graph_expr_parser import graph_expr_to_sentence
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
                return resp_err("entity_id must be a positive integer", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)

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
                return resp_err("point_id must be a positive integer", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)
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
                point_id, brief=brief, stage=StageEnum.CLEAN, status=new_status
            )
            if not ok:
                return resp_err("Update failed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            return resp_ok({
                "brief": brief,
                "stage": StageEnum.CLEAN,
                "status": new_status,
                "sub_idx": sub_idx,
                "prd_idx": prd_idx,
            })
        except Exception as e:
            logger.exception("[ExtractBriefView] Error: %s", e)
            return resp_exception(e)


class AnalyzeComponentsView(APIView):
    """POST: AI 成分分析，返回 (定语-主语)-(状语-谓语)-(定语-宾语-补语) 七项。"""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err("point_id required", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            point = get_by_id(point_id)
            if not point:
                return resp_err("Knowledge point not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)
            content = (point.content or "").strip()
            if not content:
                return resp_err("Point content is empty", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            result = do_analyze_components(content)
            if not result:
                return resp_err("Analyze failed or AI unavailable", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)
            return resp_ok(result)
        except Exception as e:
            logger.exception("[AnalyzeComponentsView] Error: %s", e)
            return resp_exception(e)


class SaveComponentsView(APIView):
    """POST: 将成分分析七项保存到 Neo4j（主语/宾语/定语/补语为点，谓语为边）。"""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err("point_id required", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            point = get_by_id(point_id)
            if not point:
                return resp_err("Knowledge point not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)
            data = getattr(request, "data", None) or {}
            batch_id = point.batch_id if point.batch_id is not None else 0
            result = do_save_components(
                point_id=point_id,
                batch_id=batch_id,
                attributive_subject=data.get("attributive_subject", ""),
                subject=data.get("subject", ""),
                adverbial=data.get("adverbial", ""),
                predicate=data.get("predicate", ""),
                attributive_object=data.get("attributive_object", ""),
                object_name=data.get("object", ""),
                complement=data.get("complement", ""),
            )
            if result.get("errors"):
                return resp_err("; ".join(result["errors"]), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            # 将 (定语)-主语-谓语-(定语)-宾语-(补语) 及状语 组成 Cypher 写入 knowledge 的 graph_brief / graph_subject / graph_object
            expressions = build_graph_expressions(
                attributive_subject=data.get("attributive_subject", ""),
                subject=data.get("subject", ""),
                adverbial=data.get("adverbial", ""),
                predicate=data.get("predicate", ""),
                attributive_object=data.get("attributive_object", ""),
                object_name=data.get("object", ""),
                complement=data.get("complement", ""),
            )
            gb = expressions.get("graph_brief", "")
            gs = expressions.get("graph_subject", "")
            go = expressions.get("graph_object", "")
            update_knowledge_point(
                point_id,
                graph_brief=gb,
                graph_subject=gs,
                graph_object=go,
                graph_brief_hash=graph_string_to_hash(gb),
                graph_subject_hash=graph_string_to_hash(gs),
                graph_object_hash=graph_string_to_hash(go),
                stage=StageEnum.PARSE,
                status=KnowledgeStatusEnum.COMPLETED,
            )
            return resp_ok(result)
        except Exception as e:
            logger.exception("[SaveComponentsView] Error: %s", e)
            return resp_exception(e)


class BuildComponentsCypherView(APIView):
    """POST: 根据成分分析七项生成「成分关系」查询 Cypher（定语-主语-谓语{状语}-定语-宾语-补语）。"""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err("point_id required", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            data = getattr(request, "data", None) or {}
            default_cypher = build_components_query_cypher(
                attributive_subject=data.get("attributive_subject", ""),
                subject=data.get("subject", ""),
                adverbial=data.get("adverbial", ""),
                predicate=data.get("predicate", ""),
                attributive_object=data.get("attributive_object", ""),
                object_name=data.get("object", ""),
                complement=data.get("complement", ""),
            )
            return resp_ok({"default_cypher": default_cypher})
        except Exception as e:
            logger.exception("[BuildComponentsCypherView] Error: %s", e)
            return resp_exception(e)


class SentenceGraphView(APIView):
    """GET sentence-level SVO graph for a knowledge document."""

    def get(self, request, entity_id, *args, **kwargs):
        """Return Neo4j sentence graph (nodes, edges) for vis-network."""
        try:
            if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
                return resp_err("entity_id must be a positive integer", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)

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


class Neo4jCypherView(APIView):
    """POST: 执行 Neo4j Cypher，返回图数据 { nodes, edges } 用于前端图谱展示。"""

    def post(self, request, *args, **kwargs):
        try:
            data = getattr(request, "data", None) or {}
            cypher = (data.get("cypher") or "").strip()
            params = data.get("params")
            if not isinstance(params, dict):
                params = {}
            result = run_cypher_to_graph(cypher, params)
            if result.get("error"):
                return resp_err(result["error"], code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            return resp_ok({"nodes": result.get("nodes", []), "edges": result.get("edges", [])})
        except Exception as e:
            logger.exception("[Neo4jCypherView] Error: %s", e)
            return resp_exception(e)


class IndexVectorView(APIView):
    """POST: 向量索引。解析 graph_subject/graph_object 构建短句，生成向量写入 Mongo sub_deco/obj_deco，并回写 vec_sub_deco_id/vec_obj_deco_id。"""

    def post(self, request, point_id, *args, **kwargs):
        try:
            if point_id is None or not isinstance(point_id, int) or point_id <= 0:
                return resp_err("point_id required", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            point = get_by_id(point_id)
            if not point:
                return resp_err("Knowledge point not found", code=RET_RESOURCE_NOT_FOUND,
                                status=http_status.HTTP_200_OK)

            gs = (point.graph_subject or "").strip()
            go = (point.graph_object or "").strip()
            if not gs and not go:
                return resp_err("成分关系为空，请先保存成分关系（graph_subject/graph_object）", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)

            vec_sub_id = getattr(point, "vec_sub_deco_id", None) or ""
            vec_obj_id = getattr(point, "vec_obj_deco_id", None) or ""
            if isinstance(vec_sub_id, str):
                vec_sub_id = vec_sub_id.strip() or None
            else:
                vec_sub_id = None
            if isinstance(vec_obj_id, str):
                vec_obj_id = vec_obj_id.strip() or None
            else:
                vec_obj_id = None

            result_data = {"vec_sub_deco_id": None, "vec_obj_deco_id": None, "sentence_sub": "", "sentence_obj": ""}
            updates = {}

            sentence_sub = graph_expr_to_sentence(gs) if gs else ""
            sentence_obj = graph_expr_to_sentence(go) if go else ""
            logger.info(
                "[IndexVectorView] 向量索引短句 point_id=%s sentence_sub=%s sentence_obj=%s",
                point_id,
                sentence_sub,
                sentence_obj,
            )

            if gs:
                result_data["sentence_sub"] = sentence_sub
                if sentence_sub:
                    new_sub_id = upsert_sub_deco(point_id, sentence_sub, vec_sub_id)
                    result_data["vec_sub_deco_id"] = new_sub_id
                    updates["vec_sub_deco_id"] = new_sub_id
            if go:
                result_data["sentence_obj"] = sentence_obj
                if sentence_obj:
                    new_obj_id = upsert_obj_deco(point_id, sentence_obj, vec_obj_id)
                    result_data["vec_obj_deco_id"] = new_obj_id
                    updates["vec_obj_deco_id"] = new_obj_id

            if updates:
                update_knowledge_point(point_id, **updates)
            # 操作成功：将当前 knowledge 记录的 stage=3、status=1 写入 MySQL
            update_knowledge_point(point_id, stage=3, status=1)
            return resp_ok(result_data)
        except Exception as e:
            logger.exception("[IndexVectorView] Error: %s", e)
            return resp_exception(e)
