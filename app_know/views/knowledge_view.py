"""
Knowledge (batch) REST API: list batches, get/delete batch. entity_id = batch_id.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.repos.knowledge_point_repo import (
    list_by_batch,
    list_distinct_batch_ids,
    delete_by_batch,
)
from app_know.repos.batch_repo import delete_batch
from common.consts.response_const import RET_RESOURCE_NOT_FOUND, RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

logger = logging.getLogger(__name__)


def _parse_entity_id(entity_id) -> int:
    try:
        eid = int(entity_id) if entity_id is not None else None
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")
    if eid is None or eid <= 0:
        raise ValueError("entity_id must be a positive integer")
    return eid


def _batch_to_dict(batch_id: int, first_content: str = "") -> dict:
    return {
        "id": batch_id,
        "title": (first_content[:80] + "..." if len(first_content or "") > 80 else first_content) or f"Batch {batch_id}",
    }


class KnowledgeListView(APIView):
    """List batches (entity_id = batch_id)."""

    def get(self, request, *args, **kwargs):
        """List batches. Returns batch_ids with synthetic title from first knowledge point."""
        try:
            limit = int(with_type(request.GET.get("limit") or 100))
            if limit <= 0 or limit > 500:
                limit = 100
            batch_ids = list_distinct_batch_ids(limit=limit)
            data = []
            for bid in batch_ids:
                items, _ = list_by_batch(bid, limit=1)
                first = (items[0].content or "") if items else ""
                data.append(_batch_to_dict(bid, first))
            return resp_ok({
                "data": data,
                "total_num": len(data),
                "next_offset": None,
            })
        except Exception as e:
            logger.exception("[KnowledgeListView] Error: %s", e)
            return resp_exception(e)

    def post(self, request, *args, **kwargs):
        """Create batch: POST to upload endpoint instead. Stub returns error."""
        return resp_err("Use POST /api/know/knowledge/upload to create", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)


class KnowledgeSomeLikeView(APIView):
    """Stub: semantic search disabled (no summary mapping)."""

    def get(self, request, *args, **kwargs):
        return resp_ok([])


class KnowledgeDetailView(APIView):
    """Get or delete a batch. entity_id = batch_id."""

    def get(self, request, entity_id, *args, **kwargs):
        """Get batch: aggregated content + knowledge point count."""
        try:
            batch_id = _parse_entity_id(entity_id)
            items, total = list_by_batch(batch_id, limit=1000)
            if not items:
                raise ValueError(f"Batch {batch_id} not found")
            content = "\n".join((k.content or "") for k in sorted(items, key=lambda x: x.seq))
            first = items[0]
            return resp_ok({
                "id": batch_id,
                "title": (first.content or "")[:80] if first.content else f"Batch {batch_id}",
                "description": "",
                "content": content,
                "source_type": "batch",
                "ct": first.ct,
                "ut": max(k.ut for k in items),
            })
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeDetailView.get] Error: %s", e)
            return resp_exception(e)

    def put(self, request, entity_id, *args, **kwargs):
        """Batch update: use parse with content to replace."""
        return resp_err("Use POST .../parse with content to update batch", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

    def delete(self, request, entity_id, *args, **kwargs):
        """Delete batch (all knowledge points + batch record)."""
        try:
            batch_id = _parse_entity_id(entity_id)
            count = delete_by_batch(batch_id)
            batch_deleted = delete_batch(batch_id)
            if count == 0 and not batch_deleted:
                raise ValueError(f"Batch {batch_id} not found")
            return resp_ok({"deleted": count})
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeDetailView.delete] Error: %s", e)
            return resp_exception(e)
