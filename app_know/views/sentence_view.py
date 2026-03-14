"""
Sentence view: list sentences for a knowledge document.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.repos import knowledge_point_repo
from common.consts.response_const import RET_INVALID_PARAM, RET_RESOURCE_NOT_FOUND
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


def _knowledge_point_to_dict(k):
    return {
        "id": k.id,
        "batch_id": k.batch_id,
        "content": k.content,
        "brief": k.brief,
        "graph_brief": k.graph_brief,
        "graph_subject": k.graph_subject,
        "graph_object": k.graph_object,
        "classification": k.classification,
        "stage": k.stage,
        "status": k.status,
        "seq": k.seq,
        "ct": k.ct,
        "ut": k.ut,
    }


class SentenceListView(APIView):
    """GET sentences by kid (knowledge document id)."""

    def get(self, request, entity_id, *args, **kwargs):
        """List sentences. Query: offset, limit, stage, status."""
        try:
            if entity_id is None or not isinstance(entity_id, int) or entity_id <= 0:
                return resp_err("entity_id must be a positive integer", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            offset = int(request.GET.get("offset") or 0)
            limit = int(request.GET.get("limit") or 100)
            stage = request.GET.get("stage")
            status = request.GET.get("status")

            if stage is not None:
                try:
                    stage = int(stage)
                except (TypeError, ValueError):
                    stage = None
            if status is not None:
                try:
                    status = int(status)
                except (TypeError, ValueError):
                    status = None

            items, total = knowledge_point_repo.list_by_batch(
                batch_id=entity_id,
                stage=stage,
                status=status,
                offset=offset,
                limit=limit,
            )

            return resp_ok({
                "data": [_knowledge_point_to_dict(k) for k in items],
                "total_num": total,
                "next_offset": offset + len(items) if (offset + len(items)) < total else None,
            })
        except ValueError as e:
            logger.warning("[SentenceListView] Validation error: %s", e)
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[SentenceListView] Error: %s", e)
            return resp_exception(e)
