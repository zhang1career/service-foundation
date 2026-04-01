"""
Knowledge point repository: CRUD for KnowledgePoint (知识点, table knowledge).
"""
import logging
from typing import List, Optional, Tuple

from django.db.models import Q

from app_know.enums.classification_enum import ClassificationEnum
from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
from app_know.models import KnowledgePoint
from common.consts.query_const import LIMIT_LIST
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)

_DB = "know_rw"


def create_knowledge_point(
        content: str,
        batch_id: Optional[int] = None,
        seq: int = 0,
        classification: int = 0,
        stage: int = 0,
        status: int = 0,
) -> KnowledgePoint:
    """Create a knowledge point. Returns the created KnowledgePoint."""
    if not content or not isinstance(content, str):
        raise ValueError("content must be a non-empty string")
    now_ms = get_now_timestamp_ms()
    cls_val = int(classification) if classification is not None else ClassificationEnum.FACT
    k = KnowledgePoint(
        batch_id=batch_id,
        content=content.strip(),
        seq=seq,
        brief="",
        graph_brief="",
        graph_subject="",
        graph_object="",
        classification=cls_val,
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
        classifications: Optional[List[int]] = None,
) -> List[KnowledgePoint]:
    """Create knowledge points for a batch. classifications: list of classification ids (int)."""
    if not contents:
        return []
    result = []
    classifications = classifications or []
    for i, c in enumerate(contents):
        if not c or not str(c).strip():
            continue
        cls = classifications[i] if i < len(classifications) else ClassificationEnum.FACT
        cls = int(cls) if cls is not None else ClassificationEnum.FACT
        k = create_knowledge_point(
            content=c.strip(),
            batch_id=batch_id,
            seq=len(result),
            classification=cls,
            stage=0,
            status=KnowledgeStatusEnum.INCOMPLETE,
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
    items = list(qs[offset: offset + limit])
    return items, total


def update(kid: int, **kwargs) -> bool:
    """Update knowledge point by id."""
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return False
    allowed = {
        "brief", "graph_brief", "graph_subject", "graph_object",
        "graph_brief_hash", "graph_subject_hash", "graph_object_hash",
        "vec_sub_deco_id", "vec_obj_deco_id",
        "classification", "stage", "status", "content", "batch_id", "seq",
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    # DB columns brief/graph_brief/graph_subject/graph_object are NOT NULL; normalize None to ""
    for key in ("brief", "graph_brief", "graph_subject", "graph_object"):
        if key in updates and updates[key] is None:
            updates[key] = ""
    if not updates:
        return False
    updates["ut"] = get_now_timestamp_ms()
    updated = KnowledgePoint.objects.using(_DB).filter(id=kid).update(**updates)
    return updated > 0


def delete_by_id(kid: int) -> bool:
    """Delete one knowledge point by id. Returns True if deleted."""
    if kid is None or not isinstance(kid, int) or kid <= 0:
        return False
    try:
        deleted, _ = KnowledgePoint.objects.using(_DB).filter(id=kid).delete()
        return deleted > 0
    except Exception as e:
        logger.exception("[delete_by_id] Error: %s", e)
        return False


def get_ids_by_batch(batch_id: int) -> List[int]:
    """Get all ids for a batch."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return []
    return list(
        KnowledgePoint.objects.using(_DB)
        .filter(batch_id=batch_id)
        .values_list("id", flat=True)
    )


def list_knowledge_points(
        batch_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 100,
) -> Tuple[List[KnowledgePoint], int]:
    """List knowledge points (rows from knowledge table). Optional batch_id filter."""
    if offset < 0:
        offset = 0
    if limit <= 0 or limit > LIMIT_LIST:
        limit = min(100, LIMIT_LIST)
    qs = KnowledgePoint.objects.using(_DB)
    if batch_id is not None and isinstance(batch_id, int) and batch_id > 0:
        qs = qs.filter(batch_id=batch_id).order_by("seq")
    else:
        qs = qs.order_by("-ct")
    total = qs.count()
    items = list(qs[offset: offset + limit])
    return items, total


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


def list_by_vec_deco_ids(
        field_name: str,
        mongo_ids: List[str],
) -> List[KnowledgePoint]:
    """
    List knowledge points by vec_sub_deco_id or vec_obj_deco_id in the given list.
    field_name: 'vec_sub_deco_id' (active) or 'vec_obj_deco_id' (passive).
    mongo_ids: list of Mongo document _id strings.
    """
    if field_name not in ("vec_sub_deco_id", "vec_obj_deco_id"):
        raise ValueError("field_name must be vec_sub_deco_id or vec_obj_deco_id")
    ids = [x.strip() for x in (mongo_ids or []) if x and str(x).strip()]
    if not ids:
        return []
    return list(
        KnowledgePoint.objects.using(_DB)
        .filter(**{f"{field_name}__in": ids})
        .order_by("id")
    )


def list_by_g_brief_hashes(hashes: List[int]) -> List[KnowledgePoint]:
    """List knowledge points whose graph_brief_hash is in the given list."""
    if not hashes:
        return []
    seen = {int(h) for h in hashes if h is not None}
    if not seen:
        return []
    return list(KnowledgePoint.objects.using(_DB).filter(graph_brief_hash__in=seen).order_by("id"))


def list_by_g_brief_exact(g_brief_list: List[str]) -> List[KnowledgePoint]:
    """List knowledge points whose graph_brief is exactly in the given list (after strip)."""
    if not g_brief_list:
        return []
    seen = {str(x).strip() for x in g_brief_list if x and str(x).strip()}
    if not seen:
        return []
    return list(KnowledgePoint.objects.using(_DB).filter(graph_brief__in=seen).order_by("id"))


def list_by_g_sub_or_g_obj_exact(expressions: List[str]) -> List[KnowledgePoint]:
    """
    List knowledge points where graph_subject or graph_object exactly matches any expression.
    Uses graph_subject_hash / graph_object_hash for pre-filter, then exact match on g_sub / g_obj.
    Returns deduplicated list by id.
    """
    from app_know.services.graph_builder_agent import graph_string_to_hash

    if not expressions:
        return []
    exprs = [str(x).strip() for x in expressions if x and str(x).strip()]
    if not exprs:
        return []
    seen_ids: set = set()
    result: List[KnowledgePoint] = []
    for expr in exprs:
        h = graph_string_to_hash(expr)
        qs = KnowledgePoint.objects.using(_DB).filter(
            Q(graph_subject_hash=h, graph_subject=expr) | Q(graph_object_hash=h, graph_object=expr)
        ).order_by("id")
        for k in qs:
            if k.id not in seen_ids:
                seen_ids.add(k.id)
                result.append(k)
    return result
