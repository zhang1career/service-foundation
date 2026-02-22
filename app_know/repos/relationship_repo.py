"""
Neo4j persistence for knowledge relationships (knowledge–entity, knowledge–knowledge).
Uses app_know Neo4j client; all nodes and edges are app-scoped via app_id.
Generated.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from py2neo import Node, Relationship

from app_know.conn.neo4j import get_neo4j_client
from app_know.models.relationships import (
    APP_ID_PROP,
    ENTITY_ID_PROP,
    ENTITY_TYPE_PROP,
    KNOWLEDGE_ID_PROP,
    NODE_LABEL_ENTITY,
    NODE_LABEL_KNOWLEDGE,
    REL_TYPE_KNOWLEDGE_ENTITY,
    REL_TYPE_KNOWLEDGE_KNOWLEDGE,
    RelationshipCreateInput,
    RelationshipQueryInput,
    RelationshipQueryResult,
)

logger = logging.getLogger(__name__)

# Limit for list queries
REL_LIST_LIMIT = 1000


def _knowledge_node_props(app_id: str, knowledge_id: int) -> Dict[str, Any]:
    return {APP_ID_PROP: app_id, KNOWLEDGE_ID_PROP: knowledge_id}


def _entity_node_props(app_id: str, entity_type: str, entity_id: str) -> Dict[str, Any]:
    return {
        APP_ID_PROP: app_id,
        ENTITY_TYPE_PROP: entity_type,
        ENTITY_ID_PROP: entity_id,
    }


def _get_or_create_knowledge_node(app_id: str, knowledge_id: int, client) -> Node:
    props = _knowledge_node_props(app_id, knowledge_id)
    node = client.find_node(NODE_LABEL_KNOWLEDGE, props)
    if node is not None:
        return node
    return client.create_node(NODE_LABEL_KNOWLEDGE, props)


def _get_or_create_entity_node(app_id: str, entity_type: str, entity_id: str, client) -> Node:
    props = _entity_node_props(app_id, entity_type, entity_id)
    node = client.find_node(NODE_LABEL_ENTITY, props)
    if node is not None:
        return node
    return client.create_node(NODE_LABEL_ENTITY, props)


def _rel_type_from_input(relationship_type: str) -> str:
    if relationship_type == "knowledge_entity":
        return REL_TYPE_KNOWLEDGE_ENTITY
    if relationship_type == "knowledge_knowledge":
        return REL_TYPE_KNOWLEDGE_KNOWLEDGE
    raise ValueError(f"Unknown relationship_type: {relationship_type}")


def _rel_props(app_id: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out = {APP_ID_PROP: app_id}
    if extra:
        for k, v in extra.items():
            if k != APP_ID_PROP:
                out[k] = v
    return out


def create_relationship(inp: RelationshipCreateInput) -> Tuple[Relationship, Node, Node]:
    """
    Create a knowledge–entity or knowledge–knowledge relationship.
    Creates source/target nodes if they do not exist. Returns (relationship, start_node, end_node).
    """
    if not inp.app_id or not str(inp.app_id).strip():
        raise ValueError("app_id is required and cannot be empty")
    if inp.source_knowledge_id is None or inp.source_knowledge_id <= 0:
        raise ValueError("source_knowledge_id must be a positive integer")
    client = get_neo4j_client()
    rel_type = _rel_type_from_input(inp.relationship_type)
    start_node = _get_or_create_knowledge_node(inp.app_id, inp.source_knowledge_id, client)

    if inp.relationship_type == "knowledge_entity":
        if not inp.entity_type or not inp.entity_id:
            raise ValueError("entity_type and entity_id are required for knowledge_entity")
        end_node = _get_or_create_entity_node(
            inp.app_id, inp.entity_type.strip(), str(inp.entity_id).strip(), client
        )
    elif inp.relationship_type == "knowledge_knowledge":
        if inp.target_knowledge_id is None:
            raise ValueError("target_knowledge_id is required for knowledge_knowledge")
        end_node = _get_or_create_knowledge_node(
            inp.app_id, inp.target_knowledge_id, client
        )
    else:
        raise ValueError(f"Unknown relationship_type: {inp.relationship_type}")

    existing = client.find_relationship(start_node, end_node, rel_type)
    if existing is not None:
        # Update properties if provided
        props = _rel_props(inp.app_id, inp.properties)
        if props:
            client.update_relationship(existing, props)
        return existing, start_node, end_node

    props = _rel_props(inp.app_id, inp.properties)
    rel = client.create_relationship(start_node, end_node, rel_type, props)
    return rel, start_node, end_node


def update_relationship_by_id(
    app_id: str, relationship_id: int, properties: Dict[str, Any]
) -> Optional[Relationship]:
    """
    Update relationship by Neo4j internal id. Verifies app_id on relationship.
    Returns updated relationship or None if not found / app_id mismatch.
    """
    if not app_id or not str(app_id).strip():
        return None
    if relationship_id is None or relationship_id <= 0:
        return None
    if not isinstance(properties, dict):
        raise ValueError("properties must be a dict")
    client = get_neo4j_client()
    result = client.run(
        "MATCH ()-[r]->() WHERE id(r) = $rid RETURN r",
        {"rid": relationship_id},
    )
    record = result.single()
    if not record:
        return None
    rel = record["r"]
    if rel.get(APP_ID_PROP) != app_id:
        return None
    # Merge props (do not overwrite app_id with wrong value)
    merged = dict(properties)
    if APP_ID_PROP not in merged:
        merged[APP_ID_PROP] = app_id
    client.update_relationship(rel, merged)
    return rel


def get_relationship_by_id(app_id: str, relationship_id: int) -> Optional[Relationship]:
    """Get relationship by Neo4j id; returns None if not found or app_id mismatch."""
    if not app_id or not str(app_id).strip():
        return None
    if relationship_id is None or relationship_id <= 0:
        return None
    client = get_neo4j_client()
    result = client.run(
        "MATCH ()-[r]->() WHERE id(r) = $rid RETURN r",
        {"rid": relationship_id},
    )
    record = result.single()
    if not record:
        return None
    rel = record["r"]
    if rel.get(APP_ID_PROP) != app_id:
        return None
    return rel


def query_relationships(inp: RelationshipQueryInput) -> Tuple[List[RelationshipQueryResult], int]:
    """
    Query relationships by app_id and optional filters.
    Returns (list of RelationshipQueryResult, total count).
    """
    if not inp.app_id or not str(inp.app_id).strip():
        raise ValueError("app_id is required and cannot be empty")
    client = get_neo4j_client()
    limit = min(max(1, inp.limit), REL_LIST_LIMIT)
    offset = max(0, inp.offset)

    # Build Cypher: match (a:Knowledge)-[r:REL_TYPE]->(b) where r.app_id = $app_id
    # and optional filters on a.knowledge_id, b (Entity or Knowledge), r type
    params: Dict[str, Any] = {"app_id": inp.app_id, "limit": limit, "offset": offset}

    conditions = ["r.app_id = $app_id"]
    if inp.relationship_type:
        rel_type = _rel_type_from_input(inp.relationship_type)
        params["rel_type"] = rel_type
        conditions.append("type(r) = $rel_type")
    if inp.knowledge_id is not None:
        params["knowledge_id"] = inp.knowledge_id
        conditions.append(
            "(a.knowledge_id = $knowledge_id OR (b:Knowledge AND b.knowledge_id = $knowledge_id))"
        )
    if inp.entity_type is not None:
        params["entity_type"] = inp.entity_type
        conditions.append("(b.entity_type = $entity_type)")
    if inp.entity_id is not None:
        params["entity_id"] = inp.entity_id
        conditions.append("(b.entity_id = $entity_id)")

    where_clause = " AND ".join(conditions)
    # Match both Knowledge->Entity and Knowledge->Knowledge; distinguish by end node label
    q = f"""
    MATCH (a:Knowledge)-[r]->(b)
    WHERE a.app_id = $app_id AND b.app_id = $app_id AND {where_clause}
    WITH a, r, b
    ORDER BY id(r)
    SKIP $offset
    LIMIT $limit
    RETURN a, r, b, labels(b) AS end_labels
    """
    count_q = f"""
    MATCH (a:Knowledge)-[r]->(b)
    WHERE a.app_id = $app_id AND b.app_id = $app_id AND {where_clause}
    RETURN count(r) AS total
    """

    try:
        total_result = client.run(count_q, params)
        total_record = total_result.single()
        total = total_record["total"] if total_record else 0
    except Exception as e:
        logger.exception("[query_relationships] count error: %s", e)
        raise

    try:
        result = client.run(q, params)
    except Exception as e:
        logger.exception("[query_relationships] query error: %s", e)
        raise

    out: List[RelationshipQueryResult] = []
    for record in result:
        a, r, b, end_labels = record["a"], record["r"], record["b"], record["end_labels"]
        rel_type_str = (
            "knowledge_knowledge" if NODE_LABEL_KNOWLEDGE in end_labels else "knowledge_entity"
        )
        source_id = a.get(KNOWLEDGE_ID_PROP)
        target_knowledge_id = b.get(KNOWLEDGE_ID_PROP) if NODE_LABEL_KNOWLEDGE in end_labels else None
        entity_type = b.get(ENTITY_TYPE_PROP) if NODE_LABEL_ENTITY in end_labels else None
        entity_id = b.get(ENTITY_ID_PROP) if NODE_LABEL_ENTITY in end_labels else None
        rel_id = r.identity if hasattr(r, "identity") else None
        props = dict(r)
        out.append(
            RelationshipQueryResult(
                relationship_id=rel_id,
                app_id=props.pop(APP_ID_PROP, inp.app_id),
                relationship_type=rel_type_str,
                source_knowledge_id=source_id,
                target_knowledge_id=target_knowledge_id,
                entity_type=entity_type,
                entity_id=entity_id,
                properties=props,
            )
        )
    return out, total


def get_related_by_knowledge_ids(
    knowledge_ids: List[int],
    app_id: str,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """
    Neo4j graph reasoning: given candidate knowledge IDs, return related knowledge and entities
    (outgoing and incoming traversals). Used by logical query to expand candidates.
    Returns list of dicts: type (knowledge|entity), knowledge_id, entity_type, entity_id,
    source_knowledge_id, hop (1). Generated.
    """
    if not app_id or not str(app_id).strip():
        raise ValueError("app_id is required and cannot be empty")
    if not isinstance(knowledge_ids, list):
        raise ValueError("knowledge_ids must be a list")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > REL_LIST_LIMIT:
        raise ValueError(f"limit must be an integer in 1..{REL_LIST_LIMIT}")
    ids = [i for i in knowledge_ids if isinstance(i, int) and i > 0]
    if not ids:
        return []
    client = get_neo4j_client()
    params: Dict[str, Any] = {"app_id": app_id, "ids": ids, "limit": limit}
    # Outgoing: (k:Knowledge)-[r]->(b) where k in ids
    q = """
    MATCH (k:Knowledge)-[r]->(b)
    WHERE k.app_id = $app_id AND b.app_id = $app_id AND k.knowledge_id IN $ids
    WITH k, b, labels(b) AS end_labels
    LIMIT $limit
    RETURN k.knowledge_id AS source_id, b, end_labels
    UNION
    MATCH (a:Knowledge)-[r]->(k:Knowledge)
    WHERE k.app_id = $app_id AND a.app_id = $app_id AND k.knowledge_id IN $ids
    WITH a, k
    LIMIT $limit
    RETURN k.knowledge_id AS source_id, a AS b, labels(a) AS end_labels
    """
    seen: set = set()
    out: List[Dict[str, Any]] = []
    try:
        result = client.run(q, params)
        for record in result:
            source_id = record["source_id"]
            b = record["b"]
            end_labels = record["end_labels"]
            if NODE_LABEL_KNOWLEDGE in end_labels:
                kid = b.get(KNOWLEDGE_ID_PROP)
                key = ("knowledge", kid)
                if key not in seen:
                    seen.add(key)
                    out.append({
                        "type": "knowledge",
                        "knowledge_id": kid,
                        "entity_type": None,
                        "entity_id": None,
                        "source_knowledge_id": source_id,
                        "hop": 1,
                    })
            else:
                etype = b.get(ENTITY_TYPE_PROP)
                eid = b.get(ENTITY_ID_PROP)
                key = ("entity", etype, eid)
                if key not in seen:
                    seen.add(key)
                    out.append({
                        "type": "entity",
                        "knowledge_id": None,
                        "entity_type": etype,
                        "entity_id": eid,
                        "source_knowledge_id": source_id,
                        "hop": 1,
                    })
            if len(out) >= limit:
                break
    except Exception as e:
        logger.exception("[get_related_by_knowledge_ids] Error: %s", e)
        raise
    return out
