"""
Relation extraction service using TextAI.
Extracts predicate logic triples (subject, predicate, object) from knowledge content.
Stores nodes in MongoDB Atlas and creates relationships in Neo4j.
"""
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from common.consts.string_const import EMPTY_STRING
from common.drivers.neo4j_driver import Neo4jDriver
from service_foundation import settings

logger = logging.getLogger(__name__)

NODE_LABEL_GRAPH_NODE = "GraphNode"


def _sanitize_rel_type(predicate: str) -> str:
    """Convert predicate to valid Neo4j relationship type (alphanumeric + underscore)."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", (predicate or "").strip())
    return s or "related_to"

_text_ai_client = None
_neo4j_driver: Optional[Neo4jDriver] = None

EXTRACT_QUESTION = 'extract the predicate logic from the main text and write the result in the following JSON format, without any other content: {"sub": "we", "prd": "are", "obj": "the champions"}'


def _get_text_ai():
    """Get TextAI client lazily."""
    global _text_ai_client
    if _text_ai_client is not None:
        return _text_ai_client

    try:
        from common.services.ai.text_ai import TextAI
    except ImportError:
        logger.warning("[relation_extractor] TextAI not available")
        return None

    base_url = os.environ.get("AIGC_API_URL", EMPTY_STRING)
    api_key = os.environ.get("AIGC_API_KEY", EMPTY_STRING)
    model = os.environ.get("AIGC_GPT_MODEL", "gpt-4o-mini")
    if not api_key:
        logger.warning("[relation_extractor] AIGC_API_KEY not configured")
        return None

    try:
        _text_ai_client = TextAI(base_url, api_key, model)
        return _text_ai_client
    except Exception as e:
        logger.exception("[relation_extractor] Failed to create TextAI client: %s", e)
        return None


def _get_neo4j_driver() -> Neo4jDriver:
    """Get the singleton Neo4jDriver instance."""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = Neo4jDriver(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASS,
            name=settings.NEO4J_DATABASE,
        )
    return _neo4j_driver


@dataclass
class ExtractedRelation:
    """Extracted relation from content."""
    subject: str
    predicate: str
    obj: str
    subject_node_id: Optional[str] = None
    obj_node_id: Optional[str] = None
    neo4j_relationship_id: Optional[int] = None


def _parse_json_from_response(response: str) -> Optional[Dict[str, str]]:
    """
    Parse JSON from AI response.
    Handles cases where JSON is embedded in text or markdown.
    """
    if not response:
        return None
    
    json_pattern = r'\{[^{}]*"sub"[^{}]*"prd"[^{}]*"obj"[^{}]*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    if matches:
        for match in matches:
            try:
                parsed = json.loads(match)
                if "sub" in parsed and "prd" in parsed and "obj" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
    
    try:
        parsed = json.loads(response.strip())
        if "sub" in parsed and "prd" in parsed and "obj" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass
    
    code_block_pattern = r'```(?:json)?\s*(\{[^`]*\})\s*```'
    code_matches = re.findall(code_block_pattern, response, re.DOTALL)
    for match in code_matches:
        try:
            parsed = json.loads(match)
            if "sub" in parsed and "prd" in parsed and "obj" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    
    return None


def _parse_multiple_json_from_response(response: str) -> List[Dict[str, str]]:
    """
    Parse multiple JSON objects from AI response.
    Returns list of parsed relations.
    """
    if not response:
        return []
    
    results = []
    
    json_pattern = r'\{[^{}]*"sub"[^{}]*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if "sub" in parsed and "prd" in parsed and "obj" in parsed:
                results.append(parsed)
        except json.JSONDecodeError:
            continue
    
    if not results:
        single = _parse_json_from_response(response)
        if single:
            results.append(single)
    
    return results


def extract_relations_from_content(
    content: str,
    app_id: int,
    knowledge_id: int,
) -> List[ExtractedRelation]:
    """
    Extract predicate logic relations from content using TextAI.

    Args:
        content: The text content to extract relations from
        app_id: Application ID (integer) for scoping
        knowledge_id: Knowledge entity ID for reference

    Returns:
        List of ExtractedRelation objects
    """
    if not content or not isinstance(content, str):
        raise ValueError("content is required and must be a string")
    if app_id is None or not isinstance(app_id, int) or app_id < 0:
        raise ValueError("app_id is required and must be a non-negative integer")

    content = content.strip()
    if not content:
        raise ValueError("content cannot be empty")

    logger.info("[relation_extractor] extract_relations_from_content input content (knowledge_id=%d, len=%d): %s",
                knowledge_id, len(content), content)

    client = _get_text_ai()
    if client is None:
        raise RuntimeError("TextAI client not available")
    
    text = content[:2000] if len(content) > 2000 else content
    
    try:
        logger.info("[relation_extractor] Calling TextAI for knowledge_id: %d", knowledge_id)
        prompt, result = client.ask_and_answer(
            text=text,
            role="knowledge extraction",
            question=EXTRACT_QUESTION,
            temperature=0.3,
        )
        logger.info("[relation_extractor] TextAI response: %s", result[:500] if result else "None")
        
        if not result or result == "no":
            logger.warning("[relation_extractor] TextAI returned empty or 'no' result")
            return []
        
        parsed_list = _parse_multiple_json_from_response(result)
        if not parsed_list:
            logger.warning("[relation_extractor] Failed to parse JSON from response: %s", result[:200])
            return []
        
        relations = []
        for parsed in parsed_list:
            subject = str(parsed.get("sub", "")).strip()
            predicate = str(parsed.get("prd", "")).strip()
            obj = str(parsed.get("obj", "")).strip()
            
            if not subject or not predicate or not obj:
                logger.warning("[relation_extractor] Incomplete relation: sub=%s, prd=%s, obj=%s", 
                             subject, predicate, obj)
                continue
            
            relations.append(ExtractedRelation(
                subject=subject,
                predicate=predicate,
                obj=obj,
            ))
        
        return relations
    except Exception as e:
        logger.exception("[relation_extractor] Error extracting relations: %s", e)
        raise


def resolve_relations_via_atlas(
    relations: List[ExtractedRelation],
    app_id: int,
) -> List[ExtractedRelation]:
    """
    Resolve subject and object via Atlas vector similarity search.
    If a similar node exists in knowledge_components, use its name; otherwise keep the parsed result.
    """
    from app_know.repos import component_repo

    resolved = []
    for rel in relations:
        subject_resolved = rel.subject
        obj_resolved = rel.obj

        similar_subject = component_repo.find_similar_node(rel.subject, app_id, limit=1)
        if similar_subject and similar_subject.get("name"):
            subject_resolved = similar_subject["name"]
            logger.info("[relation_extractor] Resolved subject '%s' -> '%s'", rel.subject, subject_resolved)

        similar_obj = component_repo.find_similar_node(rel.obj, app_id, limit=1)
        if similar_obj and similar_obj.get("name"):
            obj_resolved = similar_obj["name"]
            logger.info("[relation_extractor] Resolved object '%s' -> '%s'", rel.obj, obj_resolved)

        resolved.append(ExtractedRelation(
            subject=subject_resolved,
            predicate=rel.predicate,
            obj=obj_resolved,
        ))
    return resolved


def store_relation_in_graph(
    relation: ExtractedRelation,
    app_id: int,
    knowledge_id: int,
) -> ExtractedRelation:
    """
    Store extracted relation in MongoDB Atlas, MySQL component mapping, and Neo4j.
    
    1. Query Atlas (knowledge_components) for subject by name; if not found, insert and get _id
    2. Query Atlas for object by name; if not found, insert and get _id
    3. Insert (kid, cid, type) into table y (KnowledgeComponentMapping)
    4. Query Neo4j by cid from table y; if not found, create node with cid
    5. Check for duplicate relation in Neo4j; if not duplicate, insert relation
    
    Args:
        relation: The extracted relation
        app_id: Application ID
        knowledge_id: Source knowledge ID
    
    Returns:
        Updated ExtractedRelation with node IDs and relationship ID
    """
    from app_know.repos import component_repo
    from app_know.repos.component_mapping_repo import (
        create_mapping,
        TYPE_SUBJECT,
        TYPE_OBJECT,
    )

    subject_node = component_repo.get_or_create_node(
        name=relation.subject,
        app_id=app_id,
        node_type="entity",
    )
    subject_cid = subject_node["id"]
    relation.subject_node_id = subject_cid
    logger.info("[relation_extractor] Subject node: %s (is_new=%s)",
                subject_cid, subject_node.get("is_new"))

    obj_node = component_repo.get_or_create_node(
        name=relation.obj,
        app_id=app_id,
        node_type="entity",
    )
    obj_cid = obj_node["id"]
    relation.obj_node_id = obj_cid
    logger.info("[relation_extractor] Object node: %s (is_new=%s)",
                obj_cid, obj_node.get("is_new"))

    create_mapping(
        knowledge_id=knowledge_id,
        component_id=subject_cid,
        app_id=app_id,
        component_type=TYPE_SUBJECT,
    )
    create_mapping(
        knowledge_id=knowledge_id,
        component_id=obj_cid,
        app_id=app_id,
        component_type=TYPE_OBJECT,
    )

    driver = _get_neo4j_driver()

    subject_neo4j_node = _get_or_create_neo4j_node(
        driver=driver,
        cid=subject_cid,
        name=relation.subject,
        app_id=app_id,
    )

    obj_neo4j_node = _get_or_create_neo4j_node(
        driver=driver,
        cid=obj_cid,
        name=relation.obj,
        app_id=app_id,
    )
    
    predicate_val = (relation.predicate or "").strip() or ""
    if not predicate_val:
        predicate_val = "related_to"
        logger.warning("[relation_extractor] Empty predicate, using default 'related_to'")

    rel_type = _sanitize_rel_type(predicate_val)
    props = {"app_id": app_id, "knowledge_id": knowledge_id}

    existing_rel = driver.find_an_edge(subject_neo4j_node, obj_neo4j_node, rel_type)
    if existing_rel is not None:
        driver.update_edge(existing_rel, props)
        relation.neo4j_relationship_id = existing_rel.identity if hasattr(existing_rel, "identity") else None
        logger.info("[relation_extractor] Updated existing relationship id=%s type=%s",
                    relation.neo4j_relationship_id, rel_type)
    else:
        new_rel = driver.create_edge(subject_neo4j_node, obj_neo4j_node, rel_type, props)
        relation.neo4j_relationship_id = new_rel.identity if hasattr(new_rel, "identity") else None
        logger.info("[relation_extractor] Created new relationship id=%s type=%s",
                    relation.neo4j_relationship_id, rel_type)
    
    return relation


def _get_or_create_neo4j_node(driver: Neo4jDriver, cid: str, name: str, app_id: int):
    """Get or create a Neo4j node using cid (Atlas _id) as unique identifier."""
    props = {"cid": cid, "app_id": app_id}
    node = driver.find_node(NODE_LABEL_GRAPH_NODE, props)
    if node is not None:
        if node.get("name") != name:
            driver.update_node(node, {"name": name})
        return node

    node_props = {
        "cid": cid,
        "name": name,
        "app_id": app_id,
    }
    return driver.create_node(NODE_LABEL_GRAPH_NODE, node_props)


def extract_and_store_relations(
    content: str,
    app_id: int,
    knowledge_id: int,
) -> List[Dict[str, Any]]:
    """
    Main entry point: extract relations from content and store in graph databases.
    
    Args:
        content: Text content to extract relations from
        app_id: Application ID
        knowledge_id: Knowledge entity ID
    
    Returns:
        List of dicts with relation details
    """
    relations = extract_relations_from_content(content, app_id, knowledge_id)
    
    results = []
    for relation in relations:
        try:
            stored = store_relation_in_graph(relation, app_id, knowledge_id)
            results.append({
                "subject": stored.subject,
                "predicate": stored.predicate,
                "object": stored.obj,
                "subject_node_id": stored.subject_node_id,
                "object_node_id": stored.obj_node_id,
                "neo4j_relationship_id": stored.neo4j_relationship_id,
            })
        except Exception as e:
            logger.exception("[relation_extractor] Error storing relation: %s", e)
            results.append({
                "subject": relation.subject,
                "predicate": relation.predicate,
                "object": relation.obj,
                "error": str(e),
            })
    
    return results
