"""
Perspective Engine: project knowledge graph from a given perspective (focal entity/concept).
Returns subgraph filtered by perspective focal node.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.services.graph_builder_agent import get_sentence_graph

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
    if not focal:
        return get_sentence_graph(kid)
    full = get_sentence_graph(kid)
    nodes = full.get("nodes") or []
    edges = full.get("edges") or []
    # Filter: keep only nodes that match focal or are connected to focal
    focal_lower = focal.lower()
    node_ids_with_focal: set = set()
    for n in nodes:
        label = (n.get("label") or "").strip()
        if label and (focal in label or focal_lower in label.lower()):
            node_ids_with_focal.add(str(n.get("id", "")))
    if not node_ids_with_focal:
        return {"nodes": [], "edges": []}
    # Expand: include 1-hop neighbors
    connected_ids: set = set(node_ids_with_focal)
    for e in edges:
        f, t = str(e.get("from", "")), str(e.get("to", ""))
        if f in node_ids_with_focal or t in node_ids_with_focal:
            connected_ids.add(f)
            connected_ids.add(t)
    # Filter nodes and edges
    nodes_out = [n for n in nodes if str(n.get("id", "")) in connected_ids]
    edges_out = [
        e
        for e in edges
        if str(e.get("from", "")) in connected_ids and str(e.get("to", "")) in connected_ids
    ]
    return {"nodes": nodes_out, "edges": edges_out}
