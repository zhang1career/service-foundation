"""
Neo4j persistence for knowledge relationships (knowledge–entity, knowledge–knowledge).
Uses common Neo4j driver; all nodes and edges are app-scoped via app_id.
Generated.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from py2neo import Node, Relationship

from common.drivers.neo4j_driver import Neo4jDriver
from service_foundation import settings
from app_know.models.relationships import (
    APP_ID_PROP,
    ENTITY_ID_PROP,
    ENTITY_TYPE_PROP,
    KNOWLEDGE_ID_PROP,
    NODE_LABEL_ENTITY,
    NODE_LABEL_KNOWLEDGE,
    PREDICATE_PROP,
    REL_TYPE_KNOWLEDGE_ENTITY,
    REL_TYPE_KNOWLEDGE_KNOWLEDGE,
    PredicateTriple,
    RelationshipCreateInput,
    RelationshipQueryInput,
    RelationshipQueryResult,
    SubjectObject,
)

logger = logging.getLogger(__name__)

# Limit for list queries
REL_LIST_LIMIT = 1000

# Singleton driver instance (lazy initialization)
_neo4j_driver: Optional[Neo4jDriver] = None


def _get_neo4j_driver() -> Neo4jDriver:
    """Get the singleton Neo4jDriver instance for app_know."""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASS,
            name=settings.NEO4J_DATABASE,
        )
    return _neo4j_driver


def _knowledge_node_props(app_id: int, knowledge_id: int) -> Dict[str, Any]:
    return {APP_ID_PROP: app_id, KNOWLEDGE_ID_PROP: knowledge_id}


def _entity_node_props(app_id: int, entity_type: str, entity_id: str) -> Dict[str, Any]:
    return {
        APP_ID_PROP: app_id,
        ENTITY_TYPE_PROP: entity_type,
        ENTITY_ID_PROP: entity_id,
    }


def _get_or_create_knowledge_node(app_id: int, knowledge_id: int, client) -> Node:
    props = _knowledge_node_props(app_id, knowledge_id)
    node = client.find_node(NODE_LABEL_KNOWLEDGE, props)
    if node is not None:
        return node
    return client.create_node(NODE_LABEL_KNOWLEDGE, props)


def _get_or_create_entity_node(app_id: int, entity_type: str, entity_id: str, client) -> Node:
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


def _rel_props(
    app_id: int,
    predicate: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = {APP_ID_PROP: app_id}
    if predicate:
        out[PREDICATE_PROP] = predicate
    if extra:
        for k, v in extra.items():
            if k not in (APP_ID_PROP, PREDICATE_PROP):
                out[k] = v
    return out


def create_relationship(inp: RelationshipCreateInput) -> Tuple[Relationship, Node, Node]:
    """
    Create a knowledge–entity or knowledge–knowledge relationship.
    Creates source/target nodes if they do not exist. Returns (relationship, start_node, end_node).
    Supports predicate logic: Subject(source) --predicate-> Object(target).
    """
    if inp.app_id is None or not isinstance(inp.app_id, int) or inp.app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if inp.source_knowledge_id is None or inp.source_knowledge_id <= 0:
        raise ValueError("source_knowledge_id must be a positive integer")
    driver = _get_neo4j_driver()
    rel_type = _rel_type_from_input(inp.relationship_type)
    start_node = _get_or_create_knowledge_node(inp.app_id, inp.source_knowledge_id, driver)

    if inp.relationship_type == "knowledge_entity":
        if not inp.entity_type or not inp.entity_id:
            raise ValueError("entity_type and entity_id are required for knowledge_entity")
        end_node = _get_or_create_entity_node(
            inp.app_id, inp.entity_type.strip(), str(inp.entity_id).strip(), driver
        )
    elif inp.relationship_type == "knowledge_knowledge":
        if inp.target_knowledge_id is None:
            raise ValueError("target_knowledge_id is required for knowledge_knowledge")
        end_node = _get_or_create_knowledge_node(
            inp.app_id, inp.target_knowledge_id, driver
        )
    else:
        raise ValueError(f"Unknown relationship_type: {inp.relationship_type}")

    existing = driver.find_an_edge(start_node, end_node, rel_type)
    if existing is not None:
        props = _rel_props(inp.app_id, inp.predicate, inp.properties)
        if props:
            driver.update_edge(existing, props)
        return existing, start_node, end_node

    props = _rel_props(inp.app_id, inp.predicate, inp.properties)
    rel = driver.create_edge(start_node, end_node, rel_type, props)
    return rel, start_node, end_node


def update_relationship_by_id(
    app_id: int, relationship_id: int, properties: Dict[str, Any]
) -> Optional[Relationship]:
    """
    Update relationship by Neo4j internal id. Verifies app_id on relationship.
    Returns updated relationship or None if not found / app_id mismatch.
    """
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        return None
    if relationship_id is None or relationship_id <= 0:
        return None
    if not isinstance(properties, dict):
        raise ValueError("properties must be a dict")
    driver = _get_neo4j_driver()
    result = driver.run(
        "MATCH ()-[r]->() WHERE id(r) = $rid RETURN r",
        {"rid": relationship_id},
    )
    record = result.single()
    if not record:
        return None
    rel = record["r"]
    if rel.get(APP_ID_PROP) != app_id:
        return None
    merged = dict(properties)
    if APP_ID_PROP not in merged:
        merged[APP_ID_PROP] = app_id
    driver.update_edge(rel, merged)
    return rel


def get_relationship_by_id(app_id: int, relationship_id: int) -> Optional[Relationship]:
    """Get relationship by Neo4j id; returns None if not found or app_id mismatch."""
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        return None
    if relationship_id is None or relationship_id <= 0:
        return None
    driver = _get_neo4j_driver()
    result = driver.run(
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


def delete_relationship_by_id(app_id: int, relationship_id: int) -> bool:
    """
    Delete relationship by Neo4j internal id. Verifies app_id on relationship.
    Returns True if deleted, False if not found or app_id mismatch.
    """
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        return False
    if relationship_id is None or relationship_id <= 0:
        return False
    driver = _get_neo4j_driver()
    result = driver.run(
        "MATCH ()-[r]->() WHERE id(r) = $rid RETURN r",
        {"rid": relationship_id},
    )
    record = result.single()
    if not record:
        return False
    rel = record["r"]
    if rel.get(APP_ID_PROP) != app_id:
        return False
    driver.delete_edge(rel)
    return True


def query_relationships(inp: RelationshipQueryInput) -> Tuple[List[RelationshipQueryResult], int]:
    """
    Query relationships by app_id and optional filters.
    Returns (list of RelationshipQueryResult, total count).
    Supports predicate filtering.
    """
    if inp.app_id is None or not isinstance(inp.app_id, int) or inp.app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    driver = _get_neo4j_driver()
    limit = min(max(1, inp.limit), REL_LIST_LIMIT)
    offset = max(0, inp.offset)

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
    if inp.predicate is not None:
        params["predicate"] = inp.predicate
        conditions.append("r.predicate = $predicate")

    where_clause = " AND ".join(conditions)
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
        total_result = driver.run(count_q, params)
        total_record = total_result.single()
        total = total_record["total"] if total_record else 0
    except Exception as e:
        logger.exception("[query_relationships] count error: %s", e)
        raise

    try:
        result = driver.run(q, params)
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
        predicate_val = props.pop(PREDICATE_PROP, None)
        out.append(
            RelationshipQueryResult(
                relationship_id=rel_id,
                app_id=props.pop(APP_ID_PROP, inp.app_id),
                relationship_type=rel_type_str,
                source_knowledge_id=source_id,
                target_knowledge_id=target_knowledge_id,
                entity_type=entity_type,
                entity_id=entity_id,
                predicate=predicate_val,
                properties=props,
            )
        )
    return out, total


def query_relationships_as_triples(
    inp: RelationshipQueryInput,
) -> Tuple[List[PredicateTriple], int]:
    """
    Query relationships and return as predicate logic triples.
    Returns (list of PredicateTriple, total count).
    """
    results, total = query_relationships(inp)
    triples = []
    for r in results:
        subject = SubjectObject(
            node_type="knowledge",
            knowledge_id=r.source_knowledge_id,
        )
        if r.relationship_type == "knowledge_knowledge":
            obj = SubjectObject(
                node_type="knowledge",
                knowledge_id=r.target_knowledge_id,
            )
        else:
            obj = SubjectObject(
                node_type="entity",
                entity_type=r.entity_type,
                entity_id=r.entity_id,
            )
        triple = PredicateTriple(
            subject=subject,
            predicate=r.predicate or r.relationship_type,
            obj=obj,
            relationship_id=r.relationship_id,
            properties=r.properties,
        )
        triples.append(triple)
    return triples, total


def get_related_by_knowledge_ids(
    knowledge_ids: List[int],
    app_id: int,
    limit: int = 200,
    max_hops: int = 1,
    predicate_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Neo4j graph reasoning: given candidate knowledge IDs, return related knowledge and entities
    with multi-hop traversal support.

    Args:
        knowledge_ids: List of starting knowledge IDs
        app_id: Application ID for scoping
        limit: Maximum number of results
        max_hops: Maximum traversal depth (1-5)
        predicate_filter: Optional predicate to filter relationships

    Returns:
        List of dicts with: type, knowledge_id, entity_type, entity_id,
        source_knowledge_id, hop, predicate
    """
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if not isinstance(knowledge_ids, list):
        raise ValueError("knowledge_ids must be a list")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > REL_LIST_LIMIT:
        raise ValueError(f"limit must be an integer in 1..{REL_LIST_LIMIT}")
    if max_hops is None or not isinstance(max_hops, int) or max_hops < 1 or max_hops > 5:
        raise ValueError("max_hops must be an integer in 1..5")

    ids = [i for i in knowledge_ids if isinstance(i, int) and i > 0]
    if not ids:
        return []

    driver = _get_neo4j_driver()
    params: Dict[str, Any] = {
        "app_id": app_id,
        "ids": ids,
        "limit": limit,
        "max_hops": max_hops,
    }

    predicate_condition = ""
    if predicate_filter:
        params["predicate"] = predicate_filter
        predicate_condition = "AND r.predicate = $predicate"

    q = f"""
    MATCH path = (k:Knowledge)-[r*1..{max_hops}]->(b)
    WHERE k.app_id = $app_id AND b.app_id = $app_id AND k.knowledge_id IN $ids
    {predicate_condition.replace('r.predicate', 'ALL(rel IN r WHERE rel.predicate = $predicate)') if predicate_filter else ''}
    WITH k, b, length(path) AS hop, labels(b) AS end_labels,
         [rel IN relationships(path) | rel.predicate] AS predicates
    LIMIT $limit
    RETURN k.knowledge_id AS source_id, b, end_labels, hop, predicates
    UNION
    MATCH path = (a)-[r*1..{max_hops}]->(k:Knowledge)
    WHERE k.app_id = $app_id AND a.app_id = $app_id AND k.knowledge_id IN $ids
    {predicate_condition.replace('r.predicate', 'ALL(rel IN r WHERE rel.predicate = $predicate)') if predicate_filter else ''}
    WITH a, k, length(path) AS hop, labels(a) AS end_labels,
         [rel IN relationships(path) | rel.predicate] AS predicates
    LIMIT $limit
    RETURN k.knowledge_id AS source_id, a AS b, end_labels, hop, predicates
    """

    seen: set = set()
    out: List[Dict[str, Any]] = []
    try:
        result = driver.run(q, params)
        for record in result:
            source_id = record["source_id"]
            b = record["b"]
            end_labels = record["end_labels"]
            hop = record["hop"]
            predicates = record.get("predicates", [])
            predicate = predicates[-1] if predicates else None

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
                        "hop": hop,
                        "predicate": predicate,
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
                        "hop": hop,
                        "predicate": predicate,
                    })
            if len(out) >= limit:
                break
    except Exception as e:
        logger.exception("[get_related_by_knowledge_ids] Error: %s", e)
        raise
    return out


def get_related_as_triples(
    knowledge_ids: List[int],
    app_id: int,
    limit: int = 200,
    max_hops: int = 1,
    predicate_filter: Optional[str] = None,
) -> List[PredicateTriple]:
    """
    Get related items as predicate logic triples.
    Returns list of PredicateTriple objects.
    """
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")
    if not isinstance(knowledge_ids, list):
        raise ValueError("knowledge_ids must be a list")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > REL_LIST_LIMIT:
        raise ValueError(f"limit must be an integer in 1..{REL_LIST_LIMIT}")
    if max_hops is None or not isinstance(max_hops, int) or max_hops < 1 or max_hops > 5:
        raise ValueError("max_hops must be an integer in 1..5")

    ids = [i for i in knowledge_ids if isinstance(i, int) and i > 0]
    if not ids:
        return []

    driver = _get_neo4j_driver()
    params: Dict[str, Any] = {
        "app_id": app_id,
        "ids": ids,
        "limit": limit,
    }

    predicate_condition = ""
    if predicate_filter:
        params["predicate"] = predicate_filter
        predicate_condition = "AND r.predicate = $predicate"

    q = f"""
    MATCH (a)-[r]->(b)
    WHERE a.app_id = $app_id AND b.app_id = $app_id
    AND (a.knowledge_id IN $ids OR b.knowledge_id IN $ids)
    {predicate_condition}
    WITH a, r, b, labels(a) AS start_labels, labels(b) AS end_labels
    LIMIT $limit
    RETURN a, r, b, start_labels, end_labels
    """

    triples: List[PredicateTriple] = []
    seen: set = set()
    try:
        result = driver.run(q, params)
        for record in result:
            a, r, b = record["a"], record["r"], record["b"]
            start_labels = record["start_labels"]
            end_labels = record["end_labels"]
            rel_id = r.identity if hasattr(r, "identity") else None
            props = dict(r)
            predicate = props.pop(PREDICATE_PROP, None) or type(r).__name__

            if NODE_LABEL_KNOWLEDGE in start_labels:
                subject = SubjectObject(
                    node_type="knowledge",
                    knowledge_id=a.get(KNOWLEDGE_ID_PROP),
                )
            else:
                subject = SubjectObject(
                    node_type="entity",
                    entity_type=a.get(ENTITY_TYPE_PROP),
                    entity_id=a.get(ENTITY_ID_PROP),
                )

            if NODE_LABEL_KNOWLEDGE in end_labels:
                obj = SubjectObject(
                    node_type="knowledge",
                    knowledge_id=b.get(KNOWLEDGE_ID_PROP),
                )
            else:
                obj = SubjectObject(
                    node_type="entity",
                    entity_type=b.get(ENTITY_TYPE_PROP),
                    entity_id=b.get(ENTITY_ID_PROP),
                )

            key = (subject.node_type, subject.knowledge_id or subject.entity_id,
                   predicate,
                   obj.node_type, obj.knowledge_id or obj.entity_id)
            if key not in seen:
                seen.add(key)
                props.pop(APP_ID_PROP, None)
                triples.append(PredicateTriple(
                    subject=subject,
                    predicate=predicate,
                    obj=obj,
                    relationship_id=rel_id,
                    properties=props,
                ))

            if len(triples) >= limit:
                break
    except Exception as e:
        logger.exception("[get_related_as_triples] Error: %s", e)
        raise
    return triples
