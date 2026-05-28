"""
Insight Agent: generate insights from Graphiti memory facts.
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.consts import INSIGHT_PATH_REASONING
from app_know.repos import insight_repo
from app_know.services.graphiti_knowledge_service import GraphitiKnowledgeService

logger = logging.getLogger(__name__)


def generate_path_insights(batch_id: int) -> List[Dict[str, Any]]:
    """
    Generate path reasoning insights: find A->B->C and create "A 间接导致 C".
    Returns list of insight dicts (content, type, ...).
    """
    if not batch_id or not isinstance(batch_id, int) or batch_id <= 0:
        return []
    rows = GraphitiKnowledgeService().search(query="关键事实", batch_id=batch_id, limit=20)
    if not rows:
        return []
    insights = []
    for r in rows[:20]:
        content = f"语义记忆提示：{(r.get('content') or '').strip()}"
        if not content.strip():
            continue
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
