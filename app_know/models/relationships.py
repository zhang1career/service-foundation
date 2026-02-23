"""
Neo4j relationship models and constants for knowledge–entity and knowledge–knowledge.
Supports predicate logic structure: Subject --predicate-> Object.
Generated.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Node labels (Neo4j)
NODE_LABEL_KNOWLEDGE = "Knowledge"
NODE_LABEL_ENTITY = "Entity"

# Relationship types
REL_TYPE_KNOWLEDGE_ENTITY = "RELATES_TO_ENTITY"
REL_TYPE_KNOWLEDGE_KNOWLEDGE = "RELATES_TO_KNOWLEDGE"

# Property key for multi-application scoping (all nodes and edges)
APP_ID_PROP = "app_id"

# Predicate property key (for predicate logic)
PREDICATE_PROP = "predicate"

# Node identity props (for matching)
KNOWLEDGE_ID_PROP = "knowledge_id"
ENTITY_TYPE_PROP = "entity_type"
ENTITY_ID_PROP = "entity_id"


@dataclass
class SubjectObject:
    """Represents a subject or object in predicate logic (can be Knowledge or Entity)."""

    node_type: str  # "knowledge" | "entity"
    knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out = {"node_type": self.node_type}
        if self.node_type == "knowledge":
            out["knowledge_id"] = self.knowledge_id
            if self.title:
                out["title"] = self.title
        else:
            out["entity_type"] = self.entity_type
            out["entity_id"] = self.entity_id
        return out


@dataclass
class PredicateTriple:
    """Represents a predicate logic triple: Subject --predicate-> Object."""

    subject: SubjectObject
    predicate: str
    obj: SubjectObject
    relationship_id: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject.to_dict(),
            "predicate": self.predicate,
            "object": self.obj.to_dict(),
            "relationship_id": self.relationship_id,
            "properties": self.properties,
        }


@dataclass
class RelationshipCreateInput:
    """Input for creating a knowledge–entity or knowledge–knowledge relationship."""

    app_id: int
    relationship_type: str  # "knowledge_entity" | "knowledge_knowledge"
    source_knowledge_id: int
    # For knowledge_entity: entity_type and entity_id; for knowledge_knowledge: target_knowledge_id
    target_knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    predicate: Optional[str] = None  # Predicate label for the relationship
    properties: Optional[Dict[str, Any]] = None


@dataclass
class RelationshipUpdateInput:
    """Input for updating relationship properties."""

    app_id: int
    properties: Dict[str, Any]
    predicate: Optional[str] = None


@dataclass
class RelationshipQueryResult:
    """One relationship as returned by query APIs."""

    relationship_id: Optional[int]  # Neo4j internal id if available
    app_id: int
    relationship_type: str
    source_knowledge_id: int
    target_knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    predicate: Optional[str] = None  # Predicate label
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipQueryInput:
    """Input for querying relationships."""

    app_id: int
    knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    relationship_type: Optional[str] = None
    predicate: Optional[str] = None  # Filter by predicate
    limit: int = 100
    offset: int = 0
