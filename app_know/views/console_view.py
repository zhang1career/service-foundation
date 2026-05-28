"""
Console-level APIs for Graphiti-driven insights workflow.
"""
import json
import logging
from typing import Any, Dict, List

from rest_framework.views import APIView

from app_know.enums.classification_enum import ClassificationEnum
from app_know.services.graphiti_knowledge_service import GraphitiKnowledgeService
from app_know.services.viewpoint_query_service import integrate_viewpoint_from_items
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _get_request_data(request) -> dict:
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


class ApproximateQueryView(APIView):
    """POST: Graphiti semantic retrieval. body: { text, batch_id? }."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            text = (data.get("text") or "").strip()
            if not text:
                return resp_err(code=RET_INVALID_PARAM, message="text 必填")
            raw_batch = data.get("batch_id")
            batch_id = None
            if raw_batch not in (None, ""):
                try:
                    v = int(raw_batch)
                    if v > 0:
                        batch_id = v
                except (TypeError, ValueError):
                    batch_id = None
            rows = GraphitiKnowledgeService().search(query=text, batch_id=batch_id, limit=10)
            return resp_ok({"rows": rows})
        except Exception as e:
            logger.exception("[ApproximateQueryView] %s", e)
            return resp_exception(e)


class MemoryGraphView(APIView):
    """POST: build memory graph from Graphiti. body: { query, batch_id }."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            query = (data.get("query") or "").strip()
            raw_batch = data.get("batch_id")
            if not query:
                return resp_err(code=RET_INVALID_PARAM, message="query 必填")
            try:
                batch_id = int(raw_batch)
            except (TypeError, ValueError):
                return resp_err(code=RET_INVALID_PARAM, message="batch_id 必须为正整数")
            if batch_id <= 0:
                return resp_err(code=RET_INVALID_PARAM, message="batch_id 必须为正整数")
            graph = GraphitiKnowledgeService().memory_graph(query=query, batch_id=batch_id, limit=20)
            return resp_ok({"nodes": graph.get("nodes", []), "edges": graph.get("edges", [])})
        except Exception as e:
            logger.exception("[MemoryGraphView] %s", e)
            return resp_exception(e)


class KnowledgeByBriefView(APIView):
    """POST: query knowledge by text lines. body: { lines: string[] }."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            lines = data.get("lines")
            if not isinstance(lines, list):
                lines = [lines] if lines else []
            lines = [str(x).strip() for x in lines if x and str(x).strip()]
            if not lines:
                return resp_err(code=RET_INVALID_PARAM, message="lines 必填且非空")
            raw_batch = data.get("batch_id")
            batch_id = None
            if raw_batch not in (None, ""):
                try:
                    batch_id = int(raw_batch)
                except (TypeError, ValueError):
                    batch_id = None
            all_rows: List[Dict[str, Any]] = []
            seen: set[str] = set()
            for line in lines:
                rows = GraphitiKnowledgeService().search(query=line, batch_id=batch_id, limit=5)
                for r in rows:
                    key = str(r.get("id") or "") + "|" + str(r.get("content") or "")
                    if key in seen:
                        continue
                    seen.add(key)
                    all_rows.append(
                        {
                            "id": r.get("id"),
                            "content": r.get("content", ""),
                            "classification": ClassificationEnum.FACT,
                            "classification_label": "fact",
                            "score": r.get("score", 0.0),
                            "group_id": r.get("group_id", ""),
                        }
                    )
            return resp_ok({"rows": all_rows, "viewpoint_text": ""})
        except Exception as e:
            logger.exception("[KnowledgeByBriefView] %s", e)
            return resp_exception(e)


class IntegrateViewpointView(APIView):
    """POST: integrate viewpoint from JSON items."""

    def post(self, request, *args, **kwargs):
        try:
            data = _get_request_data(request)
            items = data.get("items")
            if not isinstance(items, list):
                items = []
            viewpoint_text = integrate_viewpoint_from_items(items)
            return resp_ok({"viewpoint_text": viewpoint_text})
        except Exception as e:
            logger.exception("[IntegrateViewpointView] %s", e)
            return resp_exception(e)
