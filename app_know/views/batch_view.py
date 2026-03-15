"""
Batch REST API: create, list, get, delete, analyze for batch table.
"""
import logging

from rest_framework import status as http_status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from app_know.consts import SOURCE_TYPE_INSTANT
from app_know.repos.batch_repo import get_batch_detail, get_by_id, list_batches, count_batches, update_content
from app_know.services.batch_service import (
    create_from_text,
    create_from_upload,
    delete_batch_and_knowledge,
    analyze_batch,
)
from common.consts.response_const import RET_RESOURCE_NOT_FOUND, RET_INVALID_PARAM, RET_MISSING_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception, with_type

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _parse_entity_id(entity_id) -> int:
    try:
        eid = int(entity_id) if entity_id is not None else None
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")
    if eid is None or eid <= 0:
        raise ValueError("entity_id must be a positive integer")
    return eid


def _batch_to_dict(b) -> dict:
    """Convert Batch model to API dict. content: text (source_type=0) or file path (source_type=1)."""
    return {
        "id": b.id,
        "content": b.content or "",
        "source_type": b.source_type if b.source_type in (0, 1) else 0,
        "ct": b.ct,
        "ut": b.ut,
    }


class BatchListView(APIView):
    """List batches from batch table."""

    def get(self, request, *args, **kwargs):
        """List batches ordered by ct desc."""
        try:
            limit = int(with_type(request.GET.get("limit") or 100))
            offset = int(with_type(request.GET.get("offset") or 0))
            if limit <= 0 or limit > 500:
                limit = 100
            if offset < 0:
                offset = 0
            batches = list_batches(limit=limit, offset=offset)
            total_num = count_batches()
            data = [_batch_to_dict(b) for b in batches]
            return resp_ok({
                "data": data,
                "total_num": total_num,
                "next_offset": offset + len(data) if len(data) == limit else None,
            })
        except Exception as e:
            logger.exception("[BatchListView] Error: %s", e)
            return resp_exception(e)


class BatchDetailView(APIView):
    """Get batch detail. Returns batch record + aggregated content from knowledge points."""

    def get(self, request, entity_id, *args, **kwargs):
        """Get batch detail. 数据逻辑在 repo（含 ut 取值）."""
        try:
            batch_id = _parse_entity_id(entity_id)
            detail = get_batch_detail(batch_id)
            if not detail:
                raise ValueError(f"Batch {batch_id} not found")
            return resp_ok(detail)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchDetailView.get] Error: %s", e)
            return resp_exception(e)

    def put(self, request, entity_id, *args, **kwargs):
        """Update batch content. Only allowed for source_type=0 (text). Body: { content: string }."""
        try:
            batch_id = _parse_entity_id(entity_id)
            batch_record = get_by_id(batch_id)
            if not batch_record:
                raise ValueError(f"Batch {batch_id} not found")
            if batch_record.source_type != SOURCE_TYPE_INSTANT:
                return resp_err(
                    "Only text batches (source_type=0) can be edited",
                    code=RET_INVALID_PARAM,
                    status=http_status.HTTP_200_OK,
                )
            data = getattr(request, "data", None) or {}
            content = (data.get("content") or "").strip()
            updated = update_content(batch_id, content)
            if not updated:
                return resp_err("Update failed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
            return resp_ok({"id": batch_id})
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchDetailView.put] Error: %s", e)
            return resp_exception(e)

    def delete(self, request, entity_id, *args, **kwargs):
        """Delete batch (batch record + all knowledge points)."""
        try:
            batch_id = _parse_entity_id(entity_id)
            if not get_by_id(batch_id):
                raise ValueError(f"Batch {batch_id} not found")
            count = delete_batch_and_knowledge(batch_id)
            return resp_ok({"deleted": count})
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchDetailView.delete] Error: %s", e)
            return resp_exception(e)


class BatchCreateTextView(APIView):
    """POST: create batch from form text."""

    def post(self, request, *args, **kwargs):
        """Body: { content: string (required) }"""
        try:
            data = getattr(request, "data", None) or request.POST or {}
            content = (data.get("content") or "").strip()
            if not content:
                return resp_err("content is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)
            result = create_from_text(content)
            return resp_ok(result)
        except ValueError as e:
            logger.warning("[BatchCreateTextView] Validation error: %s", e)
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchCreateTextView] Error: %s", e)
            return resp_exception(e)


class BatchCreateUploadView(APIView):
    """POST: create batch from uploaded file."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        """Form: file (required), title (optional), parse (optional, true to run parser)."""
        try:
            file_obj = request.FILES.get("file")
            if not file_obj:
                return resp_err("file is required", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)

            if file_obj.size > MAX_FILE_SIZE:
                return resp_err(
                    f"file too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)",
                    code=RET_INVALID_PARAM,
                    status=http_status.HTTP_200_OK,
                )

            name = (file_obj.name or "").lower()
            if not name.endswith(".txt"):
                return resp_err("only .txt files allowed", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            try:
                content = file_obj.read().decode("utf-8")
            except UnicodeDecodeError as e:
                return resp_err(
                    f"file must be UTF-8 encoded: {e}",
                    code=RET_INVALID_PARAM,
                    status=http_status.HTTP_200_OK,
                )

            file_path = file_obj.name or ""

            result = create_from_upload(
                file_content=content,
                file_path=file_path,
            )
            return resp_ok(result)
        except ValueError as e:
            logger.warning("[BatchCreateUploadView] Validation error: %s", e)
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchCreateUploadView] Error: %s", e)
            return resp_exception(e)


class BatchAnalyzeView(APIView):
    """POST: split content into sentences, save to knowledge table."""

    def post(self, request, entity_id, *args, **kwargs):
        """Body: { content: string (required), use_ai_classify?, write_sentence_raw? }"""
        try:
            batch_id = _parse_entity_id(entity_id)
            if not get_by_id(batch_id):
                raise ValueError(f"Batch {batch_id} not found")

            data = getattr(request, "data", None) or {}
            content = (data.get("content") or "").strip()
            if not content:
                return resp_err("content is required in body", code=RET_MISSING_PARAM, status=http_status.HTTP_200_OK)

            use_ai_classify = data.get("use_ai_classify", True)
            write_sentence_raw = data.get("write_sentence_raw", True)

            result = analyze_batch(
                batch_id=batch_id,
                content=content,
                use_ai_classify=use_ai_classify,
                write_sentence_raw=write_sentence_raw,
            )
            return resp_ok(result)
        except ValueError as e:
            msg = str(e)
            if "not found" in msg.lower():
                return resp_err(msg, code=RET_RESOURCE_NOT_FOUND, status=http_status.HTTP_200_OK)
            return resp_err(msg, code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[BatchAnalyzeView] Error: %s", e)
            return resp_exception(e)
