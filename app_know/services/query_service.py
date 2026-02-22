"""
Logical query service: Atlas summary relevance + Neo4j graph reasoning, combined ranked results.
Generated.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.repos.relationship_repo import get_related_by_knowledge_ids
from app_know.repos.summary_repo import search_summaries_by_text, QUERY_SEARCH_MAX_LEN
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

# Default max results for combined response
DEFAULT_QUERY_LIMIT = 50


def _validate_query(query: Optional[str]) -> str:
    if query is None:
        raise ValueError("query is required")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    q = (query or "").strip()
    if not q:
        raise ValueError("query cannot be empty")
    if len(q) > QUERY_SEARCH_MAX_LEN:
        raise ValueError(f"query must not exceed {QUERY_SEARCH_MAX_LEN} characters")
    return q


def _validate_limit(limit: Optional[int]) -> int:
    if limit is None:
        return DEFAULT_QUERY_LIMIT
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
    return limit


class LogicalQueryService(Singleton):
    """
    Service for the logical query interface: (1) Atlas text search on summaries
    for candidate knowledge IDs; (2) Neo4j graph reasoning for related knowledge/entities;
    (3) combined ranked results. Generated.
    """

    def query(
        self,
        query: str,
        app_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run logical query: search Atlas by summary relevance, expand via Neo4j,
        return combined ranked results (candidates first with score, then related by hop).
        """
        q = _validate_query(query)
        limit = _validate_limit(limit)
        app_id = (app_id or "").strip() or None

        # (1) Atlas: summary relevance -> candidate knowledge IDs with score
        try:
            atlas_results = search_summaries_by_text(
                query=q,
                app_id=app_id,
                limit=limit,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.exception("[LogicalQueryService.query] Atlas search error: %s", e)
            raise

        candidate_ids = []
        candidate_map = {}  # knowledge_id -> { summary, score, item }
        for item in atlas_results:
            kid = item.get("knowledge_id")
            if kid is not None and kid not in candidate_map:
                candidate_ids.append(kid)
                candidate_map[kid] = {
                    "type": "knowledge",
                    "knowledge_id": kid,
                    "entity_type": None,
                    "entity_id": None,
                    "summary": item.get("summary", ""),
                    "score": float(item.get("score", 1.0)),
                    "source": "atlas",
                    "hop": 0,
                }

        # (2) Neo4j: graph reasoning on candidate IDs (require app_id for Neo4j)
        related: List[Dict[str, Any]] = []
        if candidate_ids and app_id:
            try:
                related = get_related_by_knowledge_ids(
                    knowledge_ids=candidate_ids,
                    app_id=app_id,
                    limit=limit * 2,
                )
            except ValueError:
                raise
            except Exception as e:
                logger.exception("[LogicalQueryService.query] Neo4j reasoning error: %s", e)
                raise

        # (3) Combine and rank: Atlas candidates first (by score), then related (by hop)
        results: List[Dict[str, Any]] = []
        seen_knowledge: set = set()
        seen_entity: set = set()

        for kid in candidate_ids:
            if kid in candidate_map and kid not in seen_knowledge:
                seen_knowledge.add(kid)
                results.append(candidate_map[kid])
                if len(results) >= limit:
                    return {"data": results, "total_num": len(results)}

        for rel in related:
            if len(results) >= limit:
                break
            if rel.get("type") == "knowledge":
                kid = rel.get("knowledge_id")
                if kid is not None and kid not in seen_knowledge:
                    seen_knowledge.add(kid)
                    results.append({
                        "type": "knowledge",
                        "knowledge_id": kid,
                        "entity_type": None,
                        "entity_id": None,
                        "summary": None,
                        "score": 0.5,
                        "source": "neo4j",
                        "hop": rel.get("hop", 1),
                        "source_knowledge_id": rel.get("source_knowledge_id"),
                    })
            else:
                etype = rel.get("entity_type")
                eid = rel.get("entity_id")
                key = (etype, eid)
                if key not in seen_entity:
                    seen_entity.add(key)
                    results.append({
                        "type": "entity",
                        "knowledge_id": None,
                        "entity_type": etype,
                        "entity_id": eid,
                        "summary": None,
                        "score": 0.5,
                        "source": "neo4j",
                        "hop": rel.get("hop", 1),
                        "source_knowledge_id": rel.get("source_knowledge_id"),
                    })

        return {"data": results, "total_num": len(results)}
