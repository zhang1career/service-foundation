"""
Graph Builder Agent: build Neo4j graph from sentence-level 主谓宾.
Creates (subject)-[predicate]->(object) edges per sentence, scoped by kid.
Nodes use sp_type=1 (名词/主语), edges use sp_type=2 (谓语) for candidate queries.
"""
import logging
import re
import time
from typing import Any, Dict, List, Optional

from common.drivers.neo4j_driver import Neo4jDriver
from service_foundation import settings

from app_know.repos import knowledge_point_repo

logger = logging.getLogger(__name__)

# Neo4j label for sentence-level SVO nodes
LABEL_SVO_NODE = "svo_entity"
# Default app_id for sentence graph (no multi-tenant)
APP_ID_SENTENCE = 0
# sp_type: 1 = 名词节点, 2 = 谓语边 (for TOP100 candidate queries)
SP_TYPE_NOUN = 1
SP_TYPE_PREDICATE = 2


def _sanitize_rel_type(predicate: str) -> str:
    """Convert predicate to valid Neo4j relationship type."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", (predicate or "").strip())
    return s or "related_to"


_neo4j_driver: Optional[Neo4jDriver] = None


def _get_driver() -> Neo4jDriver:
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASS,
            name=settings.NEO4J_DATABASE,
        )
    return _neo4j_driver


def _node_key(name: str, kid: int) -> str:
    """Unique key for node lookup: (name, kid)."""
    n = (name or "").strip()
    return f"{kid}:{n}" if n else ""


def build_graph_for_knowledge(kid: int) -> Dict[str, Any]:
    """
    Build Neo4j graph from sentences with graph_subject, graph_object.
    Creates nodes for subject/object (per kid), edges for predicate.
    Returns {created_nodes, created_edges, skipped, errors}.
    """
    if kid is None or not isinstance(kid, int) or kid <= 0:
        raise ValueError("kid must be a positive integer")
    items, _ = knowledge_point_repo.list_by_batch(kid, limit=500)
    driver = _get_driver()
    nodes_cache: Dict[str, Any] = {}  # key -> Neo4j node
    created_nodes = 0
    created_edges = 0
    skipped = 0
    errors = []

    for s in items:
        subject = (s.graph_subject or "").strip()
        obj = (s.graph_object or "").strip()
        if not subject and not obj:
            skipped += 1
            continue
        # Infer predicate from graph_brief or use default
        pred = "related_to"
        if s.graph_brief:
            m = re.search(r"谓[：:]\s*(\S+)", s.graph_brief)
            if m:
                pred = m.group(1).strip() or pred
        pred_type = _sanitize_rel_type(pred)
        if not subject:
            subject = "_"
        if not obj:
            obj = "_"
        try:
            sub_key = _node_key(subject, kid)
            obj_key = _node_key(obj, kid)
            ut_ms = int(time.time() * 1000)
            if sub_key and sub_key not in nodes_cache:
                existing = driver.find_node(
                    LABEL_SVO_NODE,
                    {"name": subject, "kid": kid, "app_id": APP_ID_SENTENCE},
                )
                if existing:
                    driver.update_node(existing, {"sp_type": SP_TYPE_NOUN, "ut": ut_ms})
                    nodes_cache[sub_key] = existing
                else:
                    node = driver.create_node(
                        LABEL_SVO_NODE,
                        {
                            "name": subject,
                            "kid": kid,
                            "app_id": APP_ID_SENTENCE,
                            "sid": s.id,
                            "sp_type": SP_TYPE_NOUN,
                            "ut": ut_ms,
                        },
                    )
                    nodes_cache[sub_key] = node
                    created_nodes += 1
            if obj_key and obj_key not in nodes_cache:
                existing = driver.find_node(
                    LABEL_SVO_NODE,
                    {"name": obj, "kid": kid, "app_id": APP_ID_SENTENCE},
                )
                if existing:
                    driver.update_node(existing, {"sp_type": SP_TYPE_NOUN, "ut": ut_ms})
                    nodes_cache[obj_key] = existing
                else:
                    node = driver.create_node(
                        LABEL_SVO_NODE,
                        {
                            "name": obj,
                            "kid": kid,
                            "app_id": APP_ID_SENTENCE,
                            "sid": s.id,
                            "sp_type": SP_TYPE_NOUN,
                            "ut": ut_ms,
                        },
                    )
                    nodes_cache[obj_key] = node
                    created_nodes += 1
            sub_node = nodes_cache.get(sub_key)
            obj_node = nodes_cache.get(obj_key)
            if sub_node and obj_node:
                existing_edge = driver.find_an_edge(sub_node, obj_node, pred_type)
                if existing_edge is None:
                    driver.create_edge(
                        sub_node,
                        obj_node,
                        pred_type,
                        {
                            "kid": kid,
                            "sid": s.id,
                            "app_id": APP_ID_SENTENCE,
                            "sp_type": SP_TYPE_PREDICATE,
                            "ut": ut_ms,
                        },
                    )
                    created_edges += 1
                else:
                    driver.update_edge(existing_edge, {"sp_type": SP_TYPE_PREDICATE, "ut": ut_ms})
        except Exception as e:
            errors.append({"sentence_id": s.id, "error": str(e)})
            logger.warning("[graph_builder] Error for sentence %s: %s", s.id, e)

    return {
        "created_nodes": created_nodes,
        "created_edges": created_edges,
        "skipped": skipped,
        "errors": errors,
    }


def get_sentence_graph(kid: int) -> Dict[str, Any]:
    """
    Fetch Neo4j subgraph for knowledge (sentence-level svo_entity).
    Returns {nodes: [{id, label}], edges: [{from, to, label}]}.
    """
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return {"nodes": [], "edges": []}
    driver = _get_driver()
    query = """
        MATCH (n:""" + LABEL_SVO_NODE + """)-[r]-(m:""" + LABEL_SVO_NODE + """)
        WHERE n.kid = $kid AND m.kid = $kid AND n.app_id = $app_id AND m.app_id = $app_id
        RETURN startNode(r) AS startNode, endNode(r) AS endNode, type(r) AS rel_type
    """
    try:
        cursor = driver.run(query, {"kid": kid, "app_id": APP_ID_SENTENCE})
        nodes_map: Dict[str, Dict[str, Any]] = {}
        edges_list: List[Dict[str, Any]] = []
        seen_edges: set = set()
        for record in cursor:
            start_node = record["startNode"]
            end_node = record["endNode"]
            rel_type = record["rel_type"] or "related_to"
            start_name = (start_node.get("name", "?") or "?").strip()
            end_name = (end_node.get("name", "?") or "?").strip()
            start_id = str(start_node.identity) if hasattr(start_node, "identity") else str(id(start_node))
            end_id = str(end_node.identity) if hasattr(end_node, "identity") else str(id(end_node))
            if start_id not in nodes_map:
                nodes_map[start_id] = {"id": start_id, "label": start_name}
            if end_id not in nodes_map:
                nodes_map[end_id] = {"id": end_id, "label": end_name}
            key = (start_id, end_id, rel_type)
            if key not in seen_edges:
                seen_edges.add(key)
                edges_list.append({"from": start_id, "to": end_id, "label": rel_type})
        return {"nodes": list(nodes_map.values()), "edges": edges_list}
    except Exception as e:
        logger.exception("[graph_builder] get_sentence_graph error: %s", e)
        return {"nodes": [], "edges": []}


def get_top_noun_nodes(limit: int = 100) -> List[str]:
    """
    Query Neo4j for noun nodes (sp_type=1), ordered by recent update (ut desc), return distinct names.
    Used as candidate subject list for 摘要 single-choice extraction.
    """
    if limit <= 0 or limit > 500:
        limit = 100
    driver = _get_driver()
    query = """
        MATCH (n:""" + LABEL_SVO_NODE + """)
        WHERE n.sp_type = $sp_type AND n.name IS NOT NULL AND trim(n.name) <> ''
        WITH n.name AS name, max(COALESCE(n.ut, 0)) AS ut
        ORDER BY ut DESC
        LIMIT $limit
        RETURN name
    """
    try:
        cursor = driver.run(query, {"sp_type": SP_TYPE_NOUN, "limit": limit})
        return [str(r["name"]).strip() for r in cursor if r.get("name")]
    except Exception as e:
        logger.warning("[graph_builder] get_top_noun_nodes error: %s", e)
        return []


def get_top_predicate_edges(limit: int = 100) -> List[str]:
    """
    Query Neo4j for predicate edges (sp_type=2), ordered by recent update (ut desc), return distinct relationship types.
    Used as candidate predicate list for 摘要 single-choice extraction.
    """
    if limit <= 0 or limit > 500:
        limit = 100
    driver = _get_driver()
    # type(r) in py2neo returns the relationship type; we need to match any svo_entity-to-svo_entity edges with sp_type=2
    query = """
        MATCH (a:""" + LABEL_SVO_NODE + """)-[r]-(b:""" + LABEL_SVO_NODE + """)
        WHERE r.sp_type = $sp_type
        WITH type(r) AS pred, max(COALESCE(r.ut, 0)) AS ut
        ORDER BY ut DESC
        LIMIT $limit
        RETURN pred
    """
    try:
        cursor = driver.run(query, {"sp_type": SP_TYPE_PREDICATE, "limit": limit})
        return [str(r["pred"]).strip() for r in cursor if r.get("pred")]
    except Exception as e:
        logger.warning("[graph_builder] get_top_predicate_edges error: %s", e)
        return []
