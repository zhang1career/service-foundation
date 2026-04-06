"""
Upload view: accept txt file (UTF-8), create batch of knowledge points, optionally parse.
"""
from __future__ import annotations

import logging

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from app_know.consts import SOURCE_TYPE_FILE
from app_know.repos.batch_repo import create_batch
from app_know.services.parser_agent import parse_and_store
from common.consts.response_const import RET_INVALID_PARAM, RET_MISSING_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"text/plain", "application/octet-stream"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_UPLOAD_TITLE = "uploaded"
_PARSE_TRUE = frozenset(("true", "1", "yes"))


def _non_empty_form_value(request, key: str) -> str | None:
    v = request.data.get(key)
    if v is not None and str(v).strip() != "":
        return str(v).strip()
    v = request.POST.get(key)
    if v is not None and str(v).strip() != "":
        return str(v).strip()
    return None


def _upload_batch_title(request, file_obj) -> str:
    title = _non_empty_form_value(request, "title")
    if title is not None:
        return title
    if file_obj.name:
        stripped = str(file_obj.name).strip()
        if stripped:
            return stripped
    return DEFAULT_UPLOAD_TITLE


def _parse_flag_requested(request) -> bool:
    raw = _non_empty_form_value(request, "parse")
    if raw is None:
        return False
    return raw.lower() in _PARSE_TRUE


class KnowledgeUploadView(APIView):
    """Upload txt file (UTF-8), create batch of knowledge points."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        """
        Upload file. Form: file (required), title (optional), parse (optional, true to run parser).
        Returns batch_id (as id) and optional sentences.
        """
        try:
            file_obj = request.FILES.get("file")
            if not file_obj:
                return resp_err(code=RET_MISSING_PARAM, message="file is required")

            if file_obj.size > MAX_FILE_SIZE:
                return resp_err(code=RET_INVALID_PARAM, message=f"file too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

            name = (file_obj.name or "").lower()
            if not name.endswith(".txt"):
                return resp_err(code=RET_INVALID_PARAM, message="only .txt files allowed")

            try:
                content = file_obj.read().decode("utf-8")
            except UnicodeDecodeError as e:
                return resp_err(code=RET_INVALID_PARAM, message=f"file must be UTF-8 encoded: {e}")

            do_parse = _parse_flag_requested(request)
            title = _upload_batch_title(request, file_obj)
            batch_record = create_batch(title=title, source_type=SOURCE_TYPE_FILE, filename=file_obj.name or None)
            batch_id = batch_record.id

            result = {"id": batch_id, "title": title, "parse": do_parse}
            if do_parse:
                try:
                    sentences = parse_and_store(
                        batch_id=batch_id,
                        content=content,
                        use_ai_classify=True,
                        write_sentence_raw=True,
                    )
                    result["sentences"] = sentences
                    result["sentence_count"] = len(sentences)
                except Exception as e:
                    logger.exception("[KnowledgeUploadView] parse failed: %s", e)
                    result["parse_error"] = str(e)
                    result["sentences"] = []

            return resp_ok(result)
        except ValueError as e:
            logger.warning("[KnowledgeUploadView] Validation error: %s", e)
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[KnowledgeUploadView] Error: %s", e)
            return resp_exception(e)
