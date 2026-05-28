"""
Perspective Engine: fetch perspective-centered graph from Graphiti memory.
"""
import logging
from typing import Dict

from app_know.services.graphiti_knowledge_service import GraphitiKnowledgeService

logger = logging.getLogger(__name__)


def get_graph_by_perspective(
        kid: int,
        focal_name: str,
) -> Dict[str, Any]:
    """
    Get subgraph for a knowledge document filtered by perspective focal entity.
    Returns nodes and edges that involve the focal entity (e.g. 尔朱荣, 军阀政治).
    """
    if not kid or not isinstance(kid, int) or kid <= 0:
        return {"nodes": [], "edges": []}
    focal = (focal_name or "").strip()
    query = focal or "关键事实"
    graph = GraphitiKnowledgeService().memory_graph(query=query, batch_id=kid, limit=20)
    return {"nodes": graph.get("nodes", []), "edges": graph.get("edges", [])}
