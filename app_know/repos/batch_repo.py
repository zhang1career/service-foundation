"""
Batch repository: CRUD for Batch (批次, table batch).
source_type: 0-instant (form text), 1-file (uploaded file).
content: source_type=0 -> text content; source_type=1 -> file path.
数据逻辑：更新内容时更新 ut；详情返回时 ut 始终为批次表记录的 ut。
"""
import logging
from typing import Any, Dict, List, Optional

from app_know.consts import SOURCE_TYPE_INSTANT
from app_know.models import Batch
from app_know.repos.knowledge_point_repo import list_by_batch
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)

_DB = "know_rw"


def create_batch(
        content: str = "",
        source_type: int = SOURCE_TYPE_INSTANT,
) -> Batch:
    """Create a batch record. Returns the created Batch (id = batch_id for knowledge)."""
    now_ms = get_now_timestamp_ms()
    b = Batch(
        content=content or "",
        source_type=source_type if source_type in (0, 1) else SOURCE_TYPE_INSTANT,
        ct=now_ms,
        ut=now_ms,
    )
    b.save(using=_DB)
    return b


def get_by_id(batch_id: int) -> Optional[Batch]:
    """Get batch by id."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return None
    try:
        return Batch.objects.using(_DB).filter(id=batch_id).first()
    except Exception as e:
        logger.exception("[get_by_id] Error: %s", e)
        return None


def get_batch_detail(batch_id: int) -> Optional[Dict[str, Any]]:
    """
    获取批次详情（含聚合内容）。数据逻辑在 repo：ut 始终为批次表记录的 ut。
    更新内容时由 update_content 更新 batch.ut，此处只读并返回。
    """
    batch_record = get_by_id(batch_id)
    if not batch_record:
        return None
    items, total = list_by_batch(batch_id, limit=1000)
    if items:
        aggregated_content = "\n".join(
            (k.content or "") for k in sorted(items, key=lambda x: x.seq)
        )
    else:
        aggregated_content = batch_record.content or ""
    return {
        "id": batch_record.id,
        "content": batch_record.content or "",
        "source_type": batch_record.source_type if batch_record.source_type in (0, 1) else 0,
        "ct": batch_record.ct,
        "ut": batch_record.ut,
        "sentence_count": total,
        "aggregated_content": aggregated_content,
    }


def list_batches(limit: int = 100, offset: int = 0) -> List[Batch]:
    """List batches ordered by ct desc."""
    if limit <= 0 or limit > 500:
        limit = 100
    return list(Batch.objects.using(_DB).order_by("-ct")[offset: offset + limit])


def count_batches() -> int:
    """Total batch count."""
    return Batch.objects.using(_DB).count()


def update_content(batch_id: int, content: str) -> bool:
    """Update batch content and ut. Only for source_type=0 (text). Returns True if updated."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return False
    now_ms = get_now_timestamp_ms()
    count = Batch.objects.using(_DB).filter(id=batch_id, source_type=SOURCE_TYPE_INSTANT).update(
        content=content or "", ut=now_ms
    )
    return count > 0


def delete_batch(batch_id: int) -> bool:
    """Delete batch by id. Returns True if deleted."""
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        return False
    count, _ = Batch.objects.using(_DB).filter(id=batch_id).delete()
    return count > 0
