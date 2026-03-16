"""
Knowledge (batch) REST API: list batches, get/delete batch. entity_id = batch_id.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.repos.knowledge_point_repo import (
    list_by_batch,
    list_distinct_batch_ids,
    list_knowledge_points,
    get_by_id,
    update as update_knowledge_point,
    delete_by_batch,
    delete_by_id as delete_knowledge_point_by_id,
)
from app_know.repos.batch_repo import delete_batch
from app_know.repos.sentence_raw_repo import delete_by_sentence_ids
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
        """List batches. Returns batch_ids with synthetic title from first knowledge point.
        Query params: limit, batch_id (optional, filter by batch id).
        """
        try:
            limit = int(with_type(request.GET.get("limit") or 100))
            if limit <= 0 or limit > 500:
                limit = 100
            batch_id_param = request.GET.get("batch_id")
            if batch_id_param is not None and batch_id_param != "":
                try:
                    bid = int(batch_id_param)
                    if bid <= 0:
                        bid = None
                except (TypeError, ValueError):
                    bid = None
                if bid is not None:
                    items, _ = list_by_batch(bid, limit=1)
                    first = (items[0].content or "") if items else ""
                    data = [_batch_to_dict(bid, first)] if items else []
                    return resp_ok({
                        "data": data,
                        "total_num": len(data),
                        "next_offset": None,
                    })
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


def _stage_label(stage_val) -> str:
    """Resolve stage number to display label (k) from StageEnum."""
    try:
        from app_know.enums.stage_enum import StageEnum
        for id_, label in StageEnum.ITEMS:
            if id_ == stage_val:
                return label
    except Exception:
        pass
    return str(stage_val) if stage_val is not None else ""


def _classification_label(classification_val) -> str:
    """Resolve classification id to code (k) from ClassificationEnum."""
    try:
        from app_know.enums.classification_enum import ClassificationEnum
        for id_, code in ClassificationEnum.ITEMS:
            if id_ == classification_val:
                return code
    except Exception:
        pass
    return str(classification_val) if classification_val is not None else ""


def _status_label(status_val) -> str:
    """Resolve status number to display label from KnowledgeStatusEnum."""
    try:
        from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
        for id_, label in KnowledgeStatusEnum.ITEMS:
            if id_ == status_val:
                return label
    except Exception:
        pass
    return str(status_val) if status_val is not None else ""


def _knowledge_point_to_dict(k) -> dict:
    """Convert KnowledgePoint to API dict."""
    content = (k.content or "").strip()
    stage_val = getattr(k, "stage", 0)
    cls_val = getattr(k, "classification", 0)
    if cls_val is None:
        cls_val = 0
    try:
        cls_val = int(cls_val)
    except (TypeError, ValueError):
        cls_val = 0
    status_val = getattr(k, "status", 0)
    return {
        "id": k.id,
        "batch_id": k.batch_id,
        "content": content,
        "content_preview": (content[:100] + "..." if len(content) > 100 else content) or "",
        "brief": (getattr(k, "brief", None) or "").strip() or "",
        "graph_subject": (getattr(k, "graph_subject", None) or "").strip() or "",
        "graph_object": (getattr(k, "graph_object", None) or "").strip() or "",
        "vec_sub_deco_id": (getattr(k, "vec_sub_deco_id", None) or "").strip() or None,
        "vec_obj_deco_id": (getattr(k, "vec_obj_deco_id", None) or "").strip() or None,
        "seq": getattr(k, "seq", 0),
        "classification": cls_val,
        "classification_label": _classification_label(cls_val),
        "stage": stage_val,
        "stage_label": _stage_label(stage_val),
        "status": status_val,
        "status_label": _status_label(status_val),
        "ct": getattr(k, "ct", 0),
        "ut": getattr(k, "ut", 0),
    }


class KnowledgeListItemsView(APIView):
    """List knowledge points (rows from knowledge table). Query params: batch_id, offset, limit."""

    def get(self, request, *args, **kwargs):
        try:
            limit = int(with_type(request.GET.get("limit") or 100))
            if limit <= 0 or limit > 500:
                limit = 100
            offset = int(with_type(request.GET.get("offset") or 0))
            if offset < 0:
                offset = 0
            batch_id_param = request.GET.get("batch_id")
            batch_id = None
            if batch_id_param not in (None, ""):
                try:
                    bid = int(batch_id_param)
                    if bid > 0:
                        batch_id = bid
                except (TypeError, ValueError):
                    pass
            items, total = list_knowledge_points(batch_id=batch_id, offset=offset, limit=limit)
            data = [_knowledge_point_to_dict(k) for k in items]
            next_offset = offset + len(data) if len(data) == limit and offset + len(data) < total else None
            return resp_ok({
                "data": data,
                "total_num": total,
                "next_offset": next_offset,
            })
        except Exception as e:
            logger.exception("[KnowledgeListItemsView] Error: %s", e)
            return resp_exception(e)


class KnowledgePointDetailView(APIView):
    """Get, update, or delete a single knowledge point by id. URL: knowledge/points/<point_id>."""

    def get(self, request, point_id, *args, **kwargs):
        try:
            kid = _parse_entity_id(point_id)
            k = get_by_id(kid)
            if not k:
                raise ValueError(f"Knowledge point {kid} not found")
            return resp_ok(_knowledge_point_to_dict(k))
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgePointDetailView.get] Error: %s", e)
            return resp_exception(e)

    def put(self, request, point_id, *args, **kwargs):
        """Update knowledge point. Body: { content?, brief?, classification?, stage?, seq?, status? }."""
        try:
            kid = _parse_entity_id(point_id)
            k = get_by_id(kid)
            if not k:
                raise ValueError(f"Knowledge point {kid} not found")
            data = getattr(request, "data", None) or {}
            updates = {}
            if "content" in data:
                updates["content"] = (data.get("content") or "").strip()
            if "brief" in data:
                updates["brief"] = (data.get("brief") or "").strip()
            if "status" in data and data["status"] is not None:
                try:
                    updates["status"] = int(data["status"])
                except (TypeError, ValueError):
                    pass
            if "classification" in data and data["classification"] is not None:
                try:
                    updates["classification"] = int(data["classification"])
                except (TypeError, ValueError):
                    pass
            if "stage" in data and data["stage"] is not None:
                try:
                    updates["stage"] = int(data["stage"])
                except (TypeError, ValueError):
                    pass
            if "seq" in data and data["seq"] is not None:
                try:
                    updates["seq"] = int(data["seq"])
                except (TypeError, ValueError):
                    pass
            if not updates:
                return resp_ok(_knowledge_point_to_dict(k))
            ok = update_knowledge_point(kid, **updates)
            if not ok:
                return resp_err("Update failed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            k = get_by_id(kid)
            return resp_ok(_knowledge_point_to_dict(k))
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgePointDetailView.put] Error: %s", e)
            return resp_exception(e)

    def delete(self, request, point_id, *args, **kwargs):
        try:
            kid = _parse_entity_id(point_id)
            k = get_by_id(kid)
            if not k:
                raise ValueError(f"Knowledge point {kid} not found")
            try:
                delete_by_sentence_ids([kid])
            except Exception as e:
                logger.warning("[KnowledgePointDetailView.delete] delete_by_sentence_ids failed: %s", e)
            deleted = delete_knowledge_point_by_id(kid)
            if not deleted:
                return resp_err("Delete failed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            return resp_ok({"deleted": 1})
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgePointDetailView.delete] Error: %s", e)
            return resp_exception(e)


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
