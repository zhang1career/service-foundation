"""
Upload view: accept txt file (UTF-8), create batch of knowledge points, optionally parse.
"""
import logging
import time

from rest_framework import status as http_status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from app_know.services.parser_agent import parse_and_store
from common.consts.response_const import RET_INVALID_PARAM, RET_MISSING_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"text/plain", "application/octet-stream"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


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

            do_parse = str(request.data.get("parse") or request.POST.get("parse") or "").lower() in ("true", "1", "yes")
            batch_id = int(time.time() * 1000)

            result = {"id": batch_id, "title": request.data.get("title") or request.POST.get("title") or file_obj.name or "uploaded", "parse": do_parse}
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
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeUploadView] Error: %s", e)
            return resp_exception(e)
