"""
Logical query service powered by Graphiti.
"""
import logging
from typing import Any, Dict, List, Optional

from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

DEFAULT_QUERY_LIMIT = 50
QUERY_SEARCH_MAX_LEN = 2000


def validate_query(query: Optional[str]) -> str:
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = query.strip()
    if not q:
        raise ValueError("query cannot be empty")
    if len(q) > QUERY_SEARCH_MAX_LEN:
        raise ValueError(f"query must not exceed {QUERY_SEARCH_MAX_LEN} characters")
    return q


def validate_limit(limit: Optional[int]) -> int:
    if limit is None:
        return DEFAULT_QUERY_LIMIT
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
    return limit


def _search_graphiti(query: str, batch_id: Optional[int], limit: int) -> List[Dict[str, Any]]:
    # Keep import lazy so pure unit tests can run without Django ORM setup.
    from app_know.services.graphiti_knowledge_service import GraphitiKnowledgeService

    return GraphitiKnowledgeService().search(query=query, batch_id=batch_id, limit=limit)


class LogicalQueryService(Singleton):
    """Graphiti search facade for /knowledge/query."""

    def query(
        self,
        query: str,
        app_id: Optional[int] = None,
        limit: Optional[int] = None,
        output_format: str = "list",
    ) -> Dict[str, Any]:
        q = validate_query(query)
        limit = validate_limit(limit)
        batch_id = None
        if app_id is not None:
            try:
                batch_id = int(app_id)
            except (TypeError, ValueError):
                batch_id = None
        rows = _search_graphiti(query=q, batch_id=batch_id, limit=limit)
        if output_format == "triple":
            triples: List[Dict[str, Any]] = []
            for r in rows:
                triples.append(
                    {
                        "subject": {"node_type": "query", "value": q},
                        "predicate": "retrieved",
                        "object": {"node_type": "fact", "value": r.get("content", "")},
                        "properties": {"score": r.get("score", 0.0), "group_id": r.get("group_id", "")},
                    }
                )
            candidates = [
                {
                    "type": "knowledge",
                    "knowledge_id": r.get("knowledge_id"),
                    "summary": r.get("content"),
                    "score": r.get("score", 0.0),
                    "source": "graphiti",
                    "hop": 0,
                    "predicate": None,
                }
                for r in rows
            ]
            return {
                "candidates": candidates,
                "triples": triples,
                "total_candidates": len(candidates),
                "total_triples": len(triples),
            }
        data: List[Dict[str, Any]] = []
        for r in rows:
            data.append(
                {
                    "type": "knowledge",
                    "knowledge_id": r.get("knowledge_id"),
                    "entity_type": None,
                    "entity_id": None,
                    "summary": r.get("content"),
                    "score": r.get("score", 0.0),
                    "source": "graphiti",
                    "hop": 0,
                    "predicate": None,
                }
            )
        return {"data": data, "total_num": len(data)}
