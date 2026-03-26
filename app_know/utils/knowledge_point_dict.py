"""KnowledgePoint model -> API/console dict (same shape as REST knowledge point detail)."""
from __future__ import annotations

from typing import Any, Dict, Optional


def _stage_label(stage_val) -> str:
    try:
        from app_know.enums.stage_enum import StageEnum

        for id_, label in StageEnum.ITEMS:
            if id_ == stage_val:
                return label
    except Exception:
        pass
    return str(stage_val) if stage_val is not None else ""


def _classification_label(classification_val) -> str:
    try:
        from app_know.enums.classification_enum import ClassificationEnum

        for id_, code in ClassificationEnum.ITEMS:
            if id_ == classification_val:
                return code
    except Exception:
        pass
    return str(classification_val) if classification_val is not None else ""


def _status_label(status_val) -> str:
    try:
        from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum

        for id_, label in KnowledgeStatusEnum.ITEMS:
            if id_ == status_val:
                return label
    except Exception:
        pass
    return str(status_val) if status_val is not None else ""


def knowledge_point_to_dict(k) -> Dict[str, Any]:
    """Convert KnowledgePoint model instance to API dict."""
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


def get_knowledge_point_detail_dict(point_id: int) -> Optional[Dict[str, Any]]:
    """Load point by id and return API-shaped dict, or None if missing."""
    from app_know.repos.knowledge_point_repo import get_by_id

    k = get_by_id(point_id)
    return knowledge_point_to_dict(k) if k else None
