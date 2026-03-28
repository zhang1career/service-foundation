"""
Legacy knowledge-entity repo API: batch-as-entity plus row operations for KnowledgeService.

Maps older CRUD (title/description/content/source_type) onto Batch + KnowledgePoint.
"""
from __future__ import annotations

import logging
import time
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

from app_know.models import Batch, KnowledgePoint
from app_know.repos.batch_repo import create_batch, delete_batch, update_content
from app_know.repos.knowledge_point_repo import (
    delete_by_batch,
    get_batch_as_entity,
    list_by_batch,
    create_knowledge_point,
    update as update_knowledge_point,
)
from common.consts.query_const import LIMIT_LIST

logger = logging.getLogger(__name__)

_DB = "know_rw"


def _dict_to_entity(d: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**d)


def get_knowledge_by_id(entity_id: Any) -> Optional[SimpleNamespace]:
    if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
        return None
    d = get_batch_as_entity(entity_id)
    return _dict_to_entity(d) if d else None


def get_knowledge_by_ids(ids: List[int]) -> List[SimpleNamespace]:
    if not ids:
        return []
    uniq = sorted({i for i in ids if isinstance(i, int) and i > 0})
    if not uniq:
        return []
    points = list(
        KnowledgePoint.objects.using(_DB).filter(id__in=uniq).order_by("id")
    )
    out: List[SimpleNamespace] = []
    for k in points:
        title = (k.content or "")[:512] or f"Knowledge {k.id}"
        out.append(
            SimpleNamespace(
                id=k.id,
                title=title,
                description="",
                content=k.content or "",
                source_type="document",
                ct=k.ct,
                ut=k.ut,
            )
        )
    return out


def list_knowledge(
    offset: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
    title: Optional[str] = None,
) -> Tuple[List[SimpleNamespace], int]:
    if offset is None or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be >= 0")
    if limit is None or not isinstance(limit, int) or limit <= 0 or limit > LIMIT_LIST:
        raise ValueError(f"limit must be in 1..{LIMIT_LIST}")
    qs = Batch.objects.using(_DB).order_by("-ct")
    if source_type is not None and str(source_type).strip():
        qs = qs.filter(id__gte=0)
    total = qs.count()
    rows = list(qs[offset : offset + limit])
    items: List[SimpleNamespace] = []
    t_prefix = str(title).strip() if title is not None and str(title).strip() else None
    for b in rows:
        d = get_batch_as_entity(b.id)
        if d is None:
            st = "instant" if b.source_type == 0 else "file"
            d = {
                "id": b.id,
                "title": (b.content or "")[:80] or f"Batch {b.id}",
                "description": "",
                "content": b.content or "",
                "source_type": st,
                "ct": b.ct,
                "ut": b.ut,
            }
        if t_prefix and not (d.get("title") or "").startswith(t_prefix):
            continue
        ent = dict(d)
        if source_type is not None and str(source_type).strip():
            ent["source_type"] = str(source_type).strip()
        items.append(_dict_to_entity(ent))
    return items, total


def create_knowledge(
    title: str,
    description: Optional[str],
    content: Optional[str],
    source_type: str,
    ct: int,
    ut: int,
) -> SimpleNamespace:
    t = (str(title).strip() if title is not None else "")
    if not t:
        raise ValueError("title is required and cannot be empty")
    desc = (
        str(description).strip()
        if description is not None and isinstance(description, str)
        else ("" if description is None else str(description).strip())
    )
    body_parts = [t]
    if desc:
        body_parts.append(desc)
    if content:
        body_parts.append(str(content))
    body = "\n\n".join(body_parts)
    batch = create_batch(content=body, source_type=0)
    create_knowledge_point(content=body, batch_id=batch.id, seq=0, status=0, stage=0)
    d = get_batch_as_entity(batch.id)
    if d is None:
        return SimpleNamespace(
            id=batch.id,
            title=t,
            description=desc or "",
            content=body,
            source_type=source_type,
            ct=ct,
            ut=ut,
        )
    d = dict(d)
    d["source_type"] = source_type
    d["description"] = desc or ""
    return _dict_to_entity(d)


def update_knowledge(entity: Any, **kwargs: Any) -> int:
    if entity is None:
        raise ValueError("entity is required")
    batch_id = getattr(entity, "id", None)
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        raise ValueError("entity is required")
    items, _ = list_by_batch(batch_id, limit=5000)
    if not items:
        return 0
    title = kwargs.get("title")
    if title is None:
        title = getattr(entity, "title", "") or ""
    else:
        title = str(title).strip()
    desc = kwargs.get("description")
    if desc is None:
        desc = getattr(entity, "description", "") or ""
    else:
        desc = str(desc).strip() if isinstance(desc, str) else str(desc)
    content = kwargs.get("content")
    if content is None:
        content = getattr(entity, "content", "") or ""
    else:
        content = str(content)
    st = kwargs.get("source_type")
    if st is None:
        st = getattr(entity, "source_type", "unknown") or "unknown"
    else:
        st = str(st).strip() or "unknown"
    body_parts = [title]
    if desc:
        body_parts.append(desc)
    if content:
        body_parts.append(content)
    body = "\n\n".join(body_parts)
    ut = kwargs.get("ut", int(time.time() * 1000))
    first = min(items, key=lambda x: x.seq)
    n = update_knowledge_point(first.id, content=body, ut=ut)
    update_content(batch_id, body)
    return int(n)


def delete_knowledge(entity_id: Any) -> bool:
    if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
        return False
    delete_by_batch(entity_id)
    return delete_batch(entity_id)
