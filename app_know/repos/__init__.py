# app_know repositories.
from app_know.repos.knowledge_point_repo import (
    create_knowledge_point,
    batch_create,
    get_by_id,
    get_batch_as_entity,
    list_by_batch,
    list_knowledge_points,
    update,
    get_ids_by_batch,
    list_distinct_batch_ids,
    delete_by_batch,
    delete_by_id,
)
from app_know.repos.relationship_repo import (
    create_relationship,
    update_relationship_by_id,
    get_relationship_by_id,
    query_relationships,
)
from app_know.repos.insight_repo import (
    create_insight,
    get_insight_by_id,
    list_insights,
    update_insight,
    delete_insight,
)

def get_knowledge_by_id(entity_id: int):
    """Backward compat: returns batch as dict (id, title, content, ...)."""
    return get_batch_as_entity(entity_id)


__all__ = [
    "create_knowledge_point",
    "batch_create",
    "get_by_id",
    "get_batch_as_entity",
    "get_knowledge_by_id",
    "list_by_batch",
    "list_knowledge_points",
    "list_distinct_batch_ids",
    "update",
    "get_ids_by_batch",
    "delete_by_batch",
    "delete_by_id",
    "create_relationship",
    "update_relationship_by_id",
    "get_relationship_by_id",
    "query_relationships",
    "create_insight",
    "get_insight_by_id",
    "list_insights",
    "update_insight",
    "delete_insight",
]
