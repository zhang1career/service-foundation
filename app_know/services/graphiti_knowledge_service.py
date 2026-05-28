"""
Graphiti-driven knowledge operations for app_know.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
from app_know.enums.stage_enum import StageEnum
from app_know.repos.knowledge_point_repo import (
    get_by_id,
    list_by_batch,
    update as update_knowledge_point,
)
from app_know.services.graphiti_client import GraphitiClient, build_message
from common.components.singleton import Singleton

logger = logging.getLogger(__name__)


def _group_id_for_batch(batch_id: int) -> str:
    return f"know-batch-{batch_id}"


class GraphitiKnowledgeService(Singleton):
    """High-level Graphiti ingestion/search wrapper."""

    def __init__(self):
        self.client = GraphitiClient()

    def ingest_point(self, point_id: int) -> Dict[str, Any]:
        point = get_by_id(point_id)
        if not point:
            raise ValueError("Knowledge point not found")
        content = (point.content or "").strip()
        if not content:
            raise ValueError("Point content is empty")
        batch_id = int(point.batch_id or 0)
        if batch_id <= 0:
            raise ValueError("Point batch_id is invalid")
        group_id = _group_id_for_batch(batch_id)
        msg = build_message(content)
        out = self.client.add_messages(group_id=group_id, messages=[msg])
        summary = content[:120]
        update_knowledge_point(
            point_id,
            brief=summary,
            stage=StageEnum.INGESTED,
            status=KnowledgeStatusEnum.COMPLETED,
        )
        return {
            "point_id": point_id,
            "batch_id": batch_id,
            "group_id": group_id,
            "brief": summary,
            "graphiti": out,
        }

    def ingest_batch(self, batch_id: int) -> Dict[str, Any]:
        points, _ = list_by_batch(batch_id, limit=5000)
        if not points:
            raise ValueError("Batch has no knowledge points")
        group_id = _group_id_for_batch(batch_id)
        messages: List[Dict[str, Any]] = []
        point_ids: List[int] = []
        for p in points:
            content = (p.content or "").strip()
            if not content:
                continue
            point_ids.append(p.id)
            messages.append(build_message(content))
        if not messages:
            raise ValueError("No valid sentence content in batch")
        out = self.client.add_messages(group_id=group_id, messages=messages)
        for p in points:
            content = (p.content or "").strip()
            update_knowledge_point(
                p.id,
                brief=(content[:120] if content else ""),
                stage=StageEnum.INGESTED,
                status=KnowledgeStatusEnum.COMPLETED if content else KnowledgeStatusEnum.INCOMPLETE,
            )
        return {
            "batch_id": batch_id,
            "group_id": group_id,
            "ingested_count": len(messages),
            "graphiti": out,
        }

    def search(self, query: str, batch_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        group_ids = [_group_id_for_batch(batch_id)] if isinstance(batch_id, int) and batch_id > 0 else None
        raw = self.client.search(query=q, max_facts=limit, group_ids=group_ids)
        rows = self._normalize_search_rows(raw)
        if rows:
            return rows[:limit]
        # Fallback when Graphiti search returns unexpected shape
        episodes = self._episodes_fallback(batch_id=batch_id, limit=limit)
        return episodes

    def memory_graph(self, query: str, batch_id: int, limit: int = 20) -> Dict[str, Any]:
        if batch_id is None or batch_id <= 0:
            raise ValueError("batch_id is required")
        q = (query or "").strip()
        if not q:
            raise ValueError("query is required")
        group_id = _group_id_for_batch(batch_id)
        raw = self.client.get_memory(
            group_id=group_id,
            center_node_uuid=None,
            messages=[build_message(q)],
            max_facts=limit,
        )
        return self._normalize_memory_graph(raw)

    def _episodes_fallback(self, batch_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
        if not isinstance(batch_id, int) or batch_id <= 0:
            return []
        group_id = _group_id_for_batch(batch_id)
        try:
            raw = self.client.get_episodes(group_id, last_n=limit)
        except Exception as e:
            logger.warning("[GraphitiKnowledgeService] episodes fallback failed: %s", e)
            return []
        rows: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            for idx, item in enumerate(raw):
                if not isinstance(item, dict):
                    continue
                content = (item.get("content") or item.get("summary") or "").strip()
                if not content:
                    continue
                rows.append(
                    {
                        "id": str(item.get("uuid") or f"episode-{idx}"),
                        "group_id": group_id,
                        "content": content,
                        "score": float(item.get("score") or 0.0),
                        "knowledge_id": None,
                        "batch_id": batch_id,
                    }
                )
        return rows

    def _normalize_search_rows(self, raw: Any) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            iterable = raw
        elif isinstance(raw, dict):
            if isinstance(raw.get("results"), list):
                iterable = raw["results"]
            elif isinstance(raw.get("facts"), list):
                iterable = raw["facts"]
            elif isinstance(raw.get("data"), list):
                iterable = raw["data"]
            else:
                iterable = []
        else:
            iterable = []
        for idx, item in enumerate(iterable):
            if not isinstance(item, dict):
                continue
            content = (
                item.get("fact")
                or item.get("content")
                or item.get("summary")
                or item.get("text")
                or ""
            )
            content = str(content).strip()
            if not content:
                continue
            candidates.append(
                {
                    "id": str(item.get("uuid") or item.get("id") or f"fact-{idx}"),
                    "group_id": str(item.get("group_id") or item.get("groupId") or ""),
                    "content": content,
                    "score": float(item.get("score") or 0.0),
                    "knowledge_id": item.get("knowledge_id"),
                    "batch_id": item.get("batch_id"),
                }
            )
        return candidates

    def _normalize_memory_graph(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            nodes_raw = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
            edges_raw = raw.get("edges") if isinstance(raw.get("edges"), list) else []
            if nodes_raw or edges_raw:
                nodes = []
                for idx, n in enumerate(nodes_raw):
                    if not isinstance(n, dict):
                        continue
                    nid = str(n.get("uuid") or n.get("id") or f"n{idx}")
                    label = str(n.get("name") or n.get("label") or n.get("summary") or nid)
                    nodes.append({"id": nid, "label": label, "nodeType": "memory"})
                edges = []
                for e in edges_raw:
                    if not isinstance(e, dict):
                        continue
                    src = str(e.get("source") or e.get("from") or "")
                    dst = str(e.get("target") or e.get("to") or "")
                    if not src or not dst:
                        continue
                    edges.append({"from": src, "to": dst, "label": str(e.get("predicate") or e.get("label") or "related")})
                return {"nodes": nodes, "edges": edges, "raw": raw}
        # Fallback: create a pseudo graph from textual facts
        rows = self._normalize_search_rows(raw)
        nodes = []
        edges = []
        root_id = "query"
        nodes.append({"id": root_id, "label": "query", "nodeType": "query"})
        for idx, r in enumerate(rows):
            nid = f"fact-{idx}"
            nodes.append({"id": nid, "label": r["content"], "nodeType": "fact"})
            edges.append({"from": root_id, "to": nid, "label": "mentions"})
        return {"nodes": nodes, "edges": edges, "raw": raw}
