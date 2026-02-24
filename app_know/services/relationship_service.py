"""
Service layer for knowledge relationship create/update/query with validation.
Generated.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.models.relationships import (
    PREDICATE_PROP,
    PredicateTriple,
    RelationshipCreateInput,
    RelationshipQueryInput,
    RelationshipQueryResult,
)
from app_know.repos.relationship_repo import (
    create_relationship as repo_create,
    delete_relationship_by_id,
    get_relationship_by_id,
    query_relationships as repo_query,
    query_relationships_as_triples,
    update_relationship_by_id,
)
from common.components.singleton import Singleton
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

ENTITY_TYPE_MAX_LEN = 128
ENTITY_ID_MAX_LEN = 512
PREDICATE_MAX_LEN = 256
RELATIONSHIP_TYPES = ("knowledge_entity", "knowledge_knowledge")


def _validate_app_id(app_id) -> int:
    """Validate and return app_id as integer. Uses summary_service validator."""
    from app_know.services.summary_service import _validate_app_id as _validate
    return _validate(app_id)


def _validate_positive_int(value: Any, name: str) -> int:
    if value is None:
        raise ValueError(f"{name} is required")
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be an integer")
    if isinstance(value, float) and value != v:
        raise ValueError(f"{name} must be an integer")
    if v <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return v


def _relationship_result_to_dict(r: RelationshipQueryResult) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "app_id": r.app_id,
        "relationship_type": r.relationship_type,
        "source_knowledge_id": r.source_knowledge_id,
        "properties": r.properties or {},
    }
    if r.relationship_id is not None:
        out["relationship_id"] = r.relationship_id
    if r.target_knowledge_id is not None:
        out["target_knowledge_id"] = r.target_knowledge_id
    if r.entity_type is not None:
        out["entity_type"] = r.entity_type
    if r.entity_id is not None:
        out["entity_id"] = r.entity_id
    if r.predicate is not None:
        out["predicate"] = r.predicate
    return out


def _validate_predicate(predicate: Optional[str]) -> Optional[str]:
    if predicate is None:
        return None
    if not isinstance(predicate, str):
        raise ValueError("predicate must be a string")
    p = predicate.strip()
    if not p:
        return None
    if len(p) > PREDICATE_MAX_LEN:
        raise ValueError(f"predicate must be at most {PREDICATE_MAX_LEN} characters")
    return p


class RelationshipService(Singleton):
    """Service for knowledge relationship create/update/query with validation."""

    def create_relationship(
        self,
        app_id,
        relationship_type: str,
        source_knowledge_id: Any,
        target_knowledge_id: Optional[Any] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        predicate: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create or upsert a knowledge–entity or knowledge–knowledge relationship.
        Supports predicate logic: Subject(source) --predicate-> Object(target).
        Returns created/updated relationship as API dict.
        """
        app_id = _validate_app_id(app_id)
        if relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"relationship_type must be one of {RELATIONSHIP_TYPES}"
            )
        source_id = _validate_positive_int(source_knowledge_id, "source_knowledge_id")
        predicate = _validate_predicate(predicate)

        if relationship_type == "knowledge_entity":
            if not entity_type or not str(entity_type).strip():
                raise ValueError("entity_type is required for knowledge_entity")
            if not entity_id or not str(entity_id).strip():
                raise ValueError("entity_id is required for knowledge_entity")
            et = str(entity_type).strip()
            eid = str(entity_id).strip()
            if len(et) > ENTITY_TYPE_MAX_LEN:
                raise ValueError(f"entity_type must be at most {ENTITY_TYPE_MAX_LEN} characters")
            if len(eid) > ENTITY_ID_MAX_LEN:
                raise ValueError(f"entity_id must be at most {ENTITY_ID_MAX_LEN} characters")
            inp = RelationshipCreateInput(
                app_id=app_id,
                relationship_type=relationship_type,
                source_knowledge_id=source_id,
                entity_type=et,
                entity_id=eid,
                predicate=predicate,
                properties=properties,
            )
        else:
            target_id = _validate_positive_int(
                target_knowledge_id, "target_knowledge_id"
            )
            inp = RelationshipCreateInput(
                app_id=app_id,
                relationship_type=relationship_type,
                source_knowledge_id=source_id,
                target_knowledge_id=target_id,
                predicate=predicate,
                properties=properties,
            )

        rel, start_node, end_node = repo_create(inp)
        rel_id = getattr(rel, "identity", None)
        props = dict(rel)
        app_id_val = props.pop("app_id", app_id)
        predicate_val = props.pop(PREDICATE_PROP, predicate)
        result = RelationshipQueryResult(
            relationship_id=rel_id,
            app_id=app_id_val,
            relationship_type=relationship_type,
            source_knowledge_id=source_id,
            target_knowledge_id=inp.target_knowledge_id,
            entity_type=inp.entity_type,
            entity_id=inp.entity_id,
            predicate=predicate_val,
            properties=props,
        )
        return _relationship_result_to_dict(result)

    def update_relationship(
        self,
        app_id: str,
        relationship_id: Any,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update relationship properties by Neo4j relationship id. Returns updated relationship."""
        app_id = _validate_app_id(app_id)
        rid = _validate_positive_int(relationship_id, "relationship_id")
        if not properties or not isinstance(properties, dict):
            raise ValueError("properties must be a non-empty dict")
        updated = update_relationship_by_id(app_id, rid, properties)
        if updated is None:
            raise ValueError(
                f"Relationship with id {relationship_id} not found or app_id mismatch"
            )
        rel_id = getattr(updated, "identity", None)
        props = dict(updated)
        app_id_val = props.pop("app_id", app_id)
        # We don't have source/target from update; return minimal dict
        return {
            "relationship_id": rel_id,
            "app_id": app_id_val,
            "properties": props,
        }

    def get_relationship(
        self, app_id: str, relationship_id: Any
    ) -> Optional[Dict[str, Any]]:
        """Get one relationship by id. Returns None if not found or app_id mismatch."""
        app_id = _validate_app_id(app_id)
        rid = _validate_positive_int(relationship_id, "relationship_id")
        rel = get_relationship_by_id(app_id, rid)
        if rel is None:
            return None
        rel_id = getattr(rel, "identity", None)
        props = dict(rel)
        app_id_val = props.pop("app_id", app_id)
        return {
            "relationship_id": rel_id,
            "app_id": app_id_val,
            "properties": props,
        }

    def delete_relationship(
        self,
        app_id: str,
        relationship_id: Any,
    ) -> bool:
        """
        Delete relationship by Neo4j relationship id.
        Returns True if deleted, raises ValueError if not found or app_id mismatch.
        """
        app_id = _validate_app_id(app_id)
        rid = _validate_positive_int(relationship_id, "relationship_id")
        deleted = delete_relationship_by_id(app_id, rid)
        if not deleted:
            raise ValueError(
                f"Relationship with id {relationship_id} not found or app_id mismatch"
            )
        return True

    def query_relationships(
        self,
        app_id: str,
        knowledge_id: Optional[Any] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        predicate: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query relationships with optional filters.
        Returns dict with data (list), total_num, next_offset.
        """
        app_id = _validate_app_id(app_id)
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit <= 0 or limit > LIMIT_LIST:
            raise ValueError(f"limit must be in 1..{LIMIT_LIST}")

        kid = None
        if knowledge_id is not None:
            kid = _validate_positive_int(knowledge_id, "knowledge_id")
        if relationship_type is not None and relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"relationship_type must be one of {RELATIONSHIP_TYPES}"
            )
        et = (entity_type or "").strip() or None
        eid = (str(entity_id).strip() or None) if entity_id is not None else None
        predicate = _validate_predicate(predicate)
        if et is not None and len(et) > ENTITY_TYPE_MAX_LEN:
            raise ValueError(f"entity_type must be at most {ENTITY_TYPE_MAX_LEN} characters")
        if eid is not None and len(eid) > ENTITY_ID_MAX_LEN:
            raise ValueError(f"entity_id must be at most {ENTITY_ID_MAX_LEN} characters")

        inp = RelationshipQueryInput(
            app_id=app_id,
            knowledge_id=kid,
            entity_type=et,
            entity_id=eid,
            relationship_type=relationship_type,
            predicate=predicate,
            limit=limit,
            offset=offset,
        )
        items, total = repo_query(inp)
        next_offset = offset + len(items) if (offset + len(items)) < total else None
        return {
            "data": [_relationship_result_to_dict(r) for r in items],
            "total_num": total,
            "next_offset": next_offset,
        }

    def query_relationships_as_triples(
        self,
        app_id: str,
        knowledge_id: Optional[Any] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        predicate: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Query relationships and return as predicate logic triples.
        Returns dict with data (list of triples), total_num, next_offset.
        """
        app_id = _validate_app_id(app_id)
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if limit <= 0 or limit > LIMIT_LIST:
            raise ValueError(f"limit must be in 1..{LIMIT_LIST}")

        kid = None
        if knowledge_id is not None:
            kid = _validate_positive_int(knowledge_id, "knowledge_id")
        if relationship_type is not None and relationship_type not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"relationship_type must be one of {RELATIONSHIP_TYPES}"
            )
        et = (entity_type or "").strip() or None
        eid = (str(entity_id).strip() or None) if entity_id is not None else None
        predicate = _validate_predicate(predicate)

        inp = RelationshipQueryInput(
            app_id=app_id,
            knowledge_id=kid,
            entity_type=et,
            entity_id=eid,
            relationship_type=relationship_type,
            predicate=predicate,
            limit=limit,
            offset=offset,
        )
        triples, total = query_relationships_as_triples(inp)
        next_offset = offset + len(triples) if (offset + len(triples)) < total else None
        return {
            "data": [t.to_dict() for t in triples],
            "total_num": total,
            "next_offset": next_offset,
        }
