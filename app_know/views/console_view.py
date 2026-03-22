"""
Console-level APIs for the 观点 (insights) page: approximate query, g_brief to Cypher, knowledge by brief.
"""
import json
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _get_request_data(request) -> dict:
    """Get POST body as dict; parse JSON from request.body when data not already parsed."""
    data = getattr(request, "data", None)
    if data is not None and isinstance(data, dict):
        return data
    raw = getattr(request, "body", None)
    if raw and (getattr(request, "content_type", "") or "").split(";")[0].strip().lower() == "application/json":
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        if isinstance(raw, str) and raw.strip():
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
    return {}


from app_know.repos.deco_repo import (
    COLLECTION_SUB_DECO,
    COLLECTION_OBJ_DECO,
    vector_search_deco,
)
from app_know.repos.knowledge_point_repo import list_by_vec_deco_ids
from app_know.services.graph_builder_agent import build_cypher_union_from_g_brief_list


class ApproximateQueryView(APIView):
    """POST: 思路近似查询。body: { text, relation_type: 'active'|'passive' }. 返回 Mongo _id 与 knowledge 映射表."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            text = (data.get("text") or "").strip()
            relation_type = (data.get("relation_type") or "active").strip().lower()
            if not text:
                return resp_err("text 必填", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            if relation_type not in ("active", "passive"):
                return resp_err("relation_type 须为 active 或 passive", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)

            coll_name = COLLECTION_SUB_DECO if relation_type == "active" else COLLECTION_OBJ_DECO
            field_name = "vec_sub_deco_id" if relation_type == "active" else "vec_obj_deco_id"

            docs = vector_search_deco(coll_name, text, limit=5)
            mongo_ids = [str(d.get("_id", "")) for d in docs if d.get("_id")]
            if not mongo_ids:
                return resp_ok({"rows": []})

            points = list_by_vec_deco_ids(field_name, mongo_ids)
            rows = []
            for k in points:
                deco_id = getattr(k, field_name) or ""
                rows.append({
                    "mongo_id": str(deco_id),
                    "knowledge_id": k.id,
                    "g_brief": (k.graph_brief or "").strip(),
                    "content": (k.content or "").strip(),
                })
            return resp_ok({"rows": rows})
        except Exception as e:
            logger.exception("[ApproximateQueryView] %s", e)
            return resp_exception(e)


class GBriefToCypherView(APIView):
    """POST: 从 g_brief 列表生成一条 Cypher（MATCH UNION）. body: { g_brief_list: string[] }."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            g_brief_list = data.get("g_brief_list")
            if not isinstance(g_brief_list, list):
                g_brief_list = [g_brief_list] if g_brief_list else []
            cypher = build_cypher_union_from_g_brief_list(g_brief_list)
            if not cypher:
                return resp_err("无法从 g_brief 解析出有效三元组", code=RET_INVALID_PARAM,
                                status=http_status.HTTP_200_OK)
            return resp_ok({"cypher": cypher})
        except Exception as e:
            logger.exception("[GBriefToCypherView] %s", e)
            return resp_exception(e)


class KnowledgeByBriefView(APIView):
    """POST: 按路径表达式查 knowledge，去重排序；可选 integrate_ai 是否返回 AI 整合文本. body: { lines: string[], integrate_ai?: bool }."""

    def post(self, request, *args, **kwargs):
        try:
            from app_know.services.viewpoint_query_service import query_knowledge_by_path_expressions
        except ImportError as e:
            logger.exception("[KnowledgeByBriefView] import: %s", e)
            return resp_exception(e)

        data = _get_request_data(request)
        lines = data.get("lines")
        if not isinstance(lines, list):
            lines = [lines] if lines else []
        lines = [str(x).strip() for x in lines if x and str(x).strip()]
        if not lines:
            return resp_err("lines 必填且非空", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

        integrate_ai = data.get("integrate_ai", False)
        result = query_knowledge_by_path_expressions(lines, integrate_ai=integrate_ai)
        return resp_ok({"rows": result["rows"], "viewpoint_text": result["viewpoint_text"]})


class IntegrateViewpointView(APIView):
    """POST: 将 JSON 编辑器的列表 [{ content, classification }] 发送给 AI 合成观点. body: { items: [{ content, classification }] }."""

    def post(self, request, *args, **kwargs):
        try:
            from app_know.services.viewpoint_query_service import integrate_viewpoint_from_items
        except ImportError as e:
            logger.exception("[IntegrateViewpointView] import: %s", e)
            return resp_exception(e)

        data = _get_request_data(request)
        items = data.get("items")
        if not isinstance(items, list):
            items = []
        viewpoint_text = integrate_viewpoint_from_items(items)
        return resp_ok({"viewpoint_text": viewpoint_text})
