"""
Neo4j relationship models and constants for knowledge–entity and knowledge–knowledge.
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

# Node identity props (for matching)
KNOWLEDGE_ID_PROP = "knowledge_id"
ENTITY_TYPE_PROP = "entity_type"
ENTITY_ID_PROP = "entity_id"


@dataclass
class RelationshipCreateInput:
    """Input for creating a knowledge–entity or knowledge–knowledge relationship."""

    app_id: str
    relationship_type: str  # "knowledge_entity" | "knowledge_knowledge"
    source_knowledge_id: int
    # For knowledge_entity: entity_type and entity_id; for knowledge_knowledge: target_knowledge_id
    target_knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class RelationshipUpdateInput:
    """Input for updating relationship properties."""

    app_id: str
    properties: Dict[str, Any]


@dataclass
class RelationshipQueryResult:
    """One relationship as returned by query APIs."""

    relationship_id: Optional[int]  # Neo4j internal id if available
    app_id: str
    relationship_type: str
    source_knowledge_id: int
    target_knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipQueryInput:
    """Input for querying relationships."""

    app_id: str
    knowledge_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    relationship_type: Optional[str] = None
    limit: int = 100
    offset: int = 0
