"""
Knowledge point repository: CRUD for KnowledgePoint (知识点, table knowledge).
"""
import logging
import time
from typing import List, Optional, Tuple

from app_know.models import KnowledgePoint
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

_DB = "know_rw"


def create_knowledge_point(
    content: str,
    batch_id: Optional[int] = None,
    seq: int = 0,
    classification: str = "",
    stage: int = 0,
    status: int = 0,
) -> KnowledgePoint:
    """Create a knowledge point. Returns the created KnowledgePoint."""
    if not content or not isinstance(content, str):
        raise ValueError("content must be a non-empty string")
    now_ms = int(time.time() * 1000)
    k = KnowledgePoint(
        batch_id=batch_id,
        content=content.strip(),
        seq=seq,
        classification=classification or "",
        stage=stage,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )
    k.save(using=_DB)
    return k


def batch_create(
    batch_id: Optional[int],
    contents: List[str],
    classifications: Optional[List[str]] = None,
) -> List[KnowledgePoint]:
    """Create knowledge points for a batch."""
    if not contents:
        return []
    result = []
    classifications = classifications or []
    for i, c in enumerate(contents):
        if not c or not str(c).strip():
            continue
        cls = classifications[i] if i < len(classifications) else ""
        k = create_knowledge_point(
            content=c.strip(),
            batch_id=batch_id,
            seq=len(result),
            classification=cls,
            stage=0,
            status=0,
        )
        result.append(k)
    return result


def get_batch_as_entity(batch_id: int) -> Optional[dict]:
    """Return batch as entity-like dict (id, title, content) for backward compat."""
    items, _ = list_by_batch(batch_id, limit=5000)
    if not items:
        return None
    content = "\n".join((k.content or "") for k in sorted(items, key=lambda x: x.seq))
    first = items[0]
    return {
        "id": batch_id,
        "title": (first.content or "")[:80] if first.content else f"Batch {batch_id}",
        "description": "",
        "content": content,
        "source_type": "batch",
        "ct": first.ct,
        "ut": max(k.ut for k in items),
    }


def get_by_id(kid: int) -> Optional[KnowledgePoint]:
    """Get knowledge point by id."""
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return None
    try:
        return KnowledgePoint.objects.using(_DB).filter(id=kid).first()
    except Exception as e:
        logger.exception("[get_by_id] Error: %s", e)
        return None


def list_by_batch(
    batch_id: int,
    stage: Optional[int] = None,
    status: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
) -> Tuple[List[KnowledgePoint], int]:
    """List knowledge points by batch_id."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        raise ValueError("batch_id must be a positive integer")
    if limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
    qs = KnowledgePoint.objects.using(_DB).filter(batch_id=batch_id).order_by("seq")
    if stage is not None:
        qs = qs.filter(stage=stage)
    if status is not None:
        qs = qs.filter(status=status)
    total = qs.count()
    items = list(qs[offset : offset + limit])
    return items, total


def update(kid: int, **kwargs) -> bool:
    """Update knowledge point by id."""
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return False
    allowed = {
        "brief", "graph_brief", "graph_subject", "graph_object",
        "classification", "stage", "status", "content", "batch_id", "seq",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["ut"] = int(time.time() * 1000)
    updated = KnowledgePoint.objects.using(_DB).filter(id=kid).update(**updates)
    return updated > 0


def get_ids_by_batch(batch_id: int) -> List[int]:
    """Get all ids for a batch."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return []
    return list(
        KnowledgePoint.objects.using(_DB)
        .filter(batch_id=batch_id)
        .values_list("id", flat=True)
    )


def list_distinct_batch_ids(limit: int = 100) -> List[int]:
    """List distinct batch_ids for batch listing (order by max ut desc)."""
    from django.db.models import Max
    qs = (
        KnowledgePoint.objects.using(_DB)
        .values("batch_id")
        .annotate(max_ut=Max("ut"))
        .filter(batch_id__isnull=False)
        .order_by("-max_ut")[:limit]
    )
    return [r["batch_id"] for r in qs if r["batch_id"]]


def delete_by_batch(batch_id: int) -> int:
    """Delete all knowledge points for a batch. Returns count deleted."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return 0
    count, _ = KnowledgePoint.objects.using(_DB).filter(batch_id=batch_id).delete()
    return count
