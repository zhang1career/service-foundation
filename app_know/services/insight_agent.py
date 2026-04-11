"""
Insight Agent: generate insights from knowledge graph.
Supports path reasoning (A->B->C => A 间接导致 C), contradiction discovery, cross-text synthesis.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.consts import INSIGHT_PATH_REASONING
from app_know.repos import insight_repo
from app_know.services.graph_builder_agent import get_sentence_graph

logger = logging.getLogger(__name__)


def _find_paths_2hop(nodes: List[Dict], edges: List[Dict]) -> List[Dict[str, Any]]:
    """
    Find 2-hop paths A -> B -> C. Returns list of {from_name, via, to_name, rel1, rel2}.
    """
    id_to_label = {str(n.get("id", "")): (n.get("label") or "?") for n in nodes}
    out_edges: Dict[str, List[tuple]] = {}  # from_id -> [(to_id, rel_type)]
    for e in edges:
        f, t, lbl = str(e.get("from", "")), str(e.get("to", "")), e.get("label") or "related_to"
        if f not in out_edges:
            out_edges[f] = []
        out_edges[f].append((t, lbl))
    paths = []
    for from_id, to_list in out_edges.items():
        for mid, rel1 in to_list:
            for to_id, rel2 in (out_edges.get(mid) or []):
                if to_id != from_id:
                    paths.append({
                        "from_name": id_to_label.get(from_id, "?"),
                        "via": id_to_label.get(mid, "?"),
                        "to_name": id_to_label.get(to_id, "?"),
                        "rel1": rel1,
                        "rel2": rel2,
                    })
    return paths


def generate_path_insights(batch_id: int) -> List[Dict[str, Any]]:
    """
    Generate path reasoning insights: find A->B->C and create "A 间接导致 C".
    Returns list of insight dicts (content, type, ...).
    """
    if not batch_id or not isinstance(batch_id, int) or batch_id <= 0:
        return []
    graph = get_sentence_graph(batch_id)
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    if not nodes or not edges:
        return []
    paths = _find_paths_2hop(nodes, edges)
    insights = []
    seen = set()
    for p in paths[:20]:  # Limit to 20
        key = (p["from_name"], p["to_name"])
        if key in seen:
            continue
        seen.add(key)
        content = f"{p['from_name']} 通过 {p['via']} 间接关联 {p['to_name']}"
        insights.append({
            "content": content,
            "type": INSIGHT_PATH_REASONING,
        })
    return insights


def generate_insights_and_store(
        batch_id: int,
        perspective: Optional[int] = None,
        types: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate insights for a batch and store in DB. batch_id groups knowledge points.
    """
    if not batch_id or not isinstance(batch_id, int) or batch_id <= 0:
        raise ValueError("batch_id must be a positive integer")
    types = types or [INSIGHT_PATH_REASONING]
    results = []
    if INSIGHT_PATH_REASONING in types:
        for item in generate_path_insights(batch_id):
            try:
                ins = insight_repo.create_insight(
                    content=item["content"],
                    type=INSIGHT_PATH_REASONING,
                    status=0,
                    perspective=perspective,
                )
                results.append({
                    "id": ins.id,
                    "content": ins.content,
                    "type": ins.type,
                    "status": ins.status,
                })
            except Exception as e:
                logger.warning("[insight_agent] Failed to save insight: %s", e)
    return results
