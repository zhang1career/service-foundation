"""
Logical query service: Atlas summary relevance + Neo4j graph reasoning, combined ranked results.
Supports multi-hop traversal, predicate filtering, and predicate logic output format.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.repos.relationship_repo import (
    get_related_as_triples,
    get_related_by_knowledge_ids,
)
from app_know.repos.summary_mapping_repo import get_knowledge_ids_by_summary_ids
from app_know.repos.summary_repo import search_summaries_by_text, QUERY_SEARCH_MAX_LEN
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

DEFAULT_QUERY_LIMIT = 50
DEFAULT_MAX_HOPS = 1
MAX_HOPS_LIMIT = 5


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


def _validate_max_hops(max_hops: Optional[int]) -> int:
    if max_hops is None:
        return DEFAULT_MAX_HOPS
    if not isinstance(max_hops, int):
        raise ValueError("max_hops must be an integer")
    if max_hops < 1 or max_hops > MAX_HOPS_LIMIT:
        raise ValueError(f"max_hops must be in 1..{MAX_HOPS_LIMIT}")
    return max_hops


class LogicalQueryService(Singleton):
    """
    Service for the logical query interface:
    (1) Atlas text search on summaries for candidate knowledge IDs
    (2) MySQL mapping to get knowledge IDs from summary IDs
    (3) Neo4j graph reasoning for related knowledge/entities with multi-hop support
    (4) Combined ranked results with optional predicate logic format
    """

    def query(
        self,
        query: str,
        app_id: Optional[int] = None,
        limit: Optional[int] = None,
        max_hops: Optional[int] = None,
        predicate_filter: Optional[str] = None,
        output_format: str = "list",
    ) -> Dict[str, Any]:
        """
        Run logical query: search Atlas by summary relevance, expand via Neo4j,
        return combined ranked results.

        Args:
            query: Search query string
            app_id: Application ID for scoping
            limit: Maximum number of results
            max_hops: Maximum traversal depth in Neo4j (1-5)
            predicate_filter: Filter relationships by predicate
            output_format: "list" for flat results, "triple" for predicate logic format

        Returns:
            Dict with data (results), total_num, and optional triples
        """
        q = _validate_query(query)
        limit = _validate_limit(limit)
        max_hops = _validate_max_hops(max_hops)
        if app_id is not None and not (isinstance(app_id, int) and app_id >= 0):
            try:
                from app_know.services.summary_service import _validate_app_id
                app_id = _validate_app_id(app_id)
            except ValueError:
                app_id = None

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
        candidate_map = {}
        summary_ids = []

        for item in atlas_results:
            kid = item.get("kid")
            summary_id = item.get("id")
            if summary_id:
                summary_ids.append(summary_id)
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
                    "predicate": None,
                }

        # (2) MySQL mapping: get additional knowledge IDs from summary IDs
        if app_id and summary_ids:
            try:
                mapped_ids = get_knowledge_ids_by_summary_ids(summary_ids, app_id=app_id)
                for kid in mapped_ids:
                    if kid not in candidate_map:
                        candidate_ids.append(kid)
                        candidate_map[kid] = {
                            "type": "knowledge",
                            "knowledge_id": kid,
                            "entity_type": None,
                            "entity_id": None,
                            "summary": None,
                            "score": 0.8,
                            "source": "mysql_mapping",
                            "hop": 0,
                            "predicate": None,
                        }
            except Exception as e:
                logger.warning("[LogicalQueryService.query] MySQL mapping error: %s", e)

        # (3) Neo4j: graph reasoning with multi-hop support
        related: List[Dict[str, Any]] = []
        triples = []

        if app_id:
            try:
                if output_format == "triple":
                    triples = get_related_as_triples(
                        knowledge_ids=candidate_ids,
                        app_id=app_id,
                        limit=limit * 2,
                        max_hops=max_hops,
                        predicate_filter=predicate_filter,
                    )
                else:
                    related = get_related_by_knowledge_ids(
                        knowledge_ids=candidate_ids,
                        app_id=app_id,
                        limit=limit * 2,
                        max_hops=max_hops,
                        predicate_filter=predicate_filter,
                    )
            except ValueError:
                raise
            except Exception as e:
                logger.exception("[LogicalQueryService.query] Neo4j reasoning error: %s", e)
                raise

        # (4) Build response based on output format
        if output_format == "triple":
            return self._build_triple_response(candidate_map, candidate_ids, triples, limit)
        else:
            return self._build_list_response(candidate_map, candidate_ids, related, limit)

    def _build_list_response(
        self,
        candidate_map: Dict[int, Dict],
        candidate_ids: List[int],
        related: List[Dict[str, Any]],
        limit: int,
    ) -> Dict[str, Any]:
        """Build flat list response format."""
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
                        "predicate": rel.get("predicate"),
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
                        "predicate": rel.get("predicate"),
                        "source_knowledge_id": rel.get("source_knowledge_id"),
                    })

        return {"data": results, "total_num": len(results)}

    def _build_triple_response(
        self,
        candidate_map: Dict[int, Dict],
        candidate_ids: List[int],
        triples,
        limit: int,
    ) -> Dict[str, Any]:
        """Build predicate logic triple response format."""
        candidates = []
        for kid in candidate_ids:
            if kid in candidate_map:
                candidates.append(candidate_map[kid])
                if len(candidates) >= limit:
                    break

        triple_dicts = [t.to_dict() for t in triples[:limit]]

        return {
            "candidates": candidates,
            "triples": triple_dicts,
            "total_candidates": len(candidates),
            "total_triples": len(triple_dicts),
        }
