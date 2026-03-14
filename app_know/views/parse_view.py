"""
Parse view: trigger parsing for a batch. entity_id = batch_id.
"""
import logging

from rest_framework import status as http_status
from rest_framework.views import APIView

from app_know.services.parser_agent import parse_and_store
from common.consts.response_const import RET_INVALID_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)


class KnowledgeParseView(APIView):
    """POST to parse content into knowledge points (sentences)."""

    def post(self, request, entity_id, *args, **kwargs):
        """
        Parse content. entity_id = batch_id. Body: content (required), use_ai_classify, write_sentence_raw.
        """
        try:
            batch_id = entity_id
            if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
                return resp_err("entity_id (batch_id) must be a positive integer", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            data = getattr(request, "data", None) or {}
            content = (data.get("content") or "").strip()
            if not content:
                return resp_err("content is required in body", code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)

            use_ai_classify = data.get("use_ai_classify", True)
            write_sentence_raw = data.get("write_sentence_raw", True)

            sentences = parse_and_store(
                batch_id=batch_id,
                content=content,
                use_ai_classify=use_ai_classify,
                write_sentence_raw=write_sentence_raw,
            )

            return resp_ok({
                "kid": batch_id,
                "sentence_count": len(sentences),
                "sentences": sentences,
            })
        except ValueError as e:
            logger.warning("[KnowledgeParseView] Validation error: %s", e)
            return resp_err(str(e), code=RET_INVALID_PARAM, status=http_status.HTTP_200_OK)
        except Exception as e:
            logger.exception("[KnowledgeParseView] Error: %s", e)
            return resp_exception(e)
