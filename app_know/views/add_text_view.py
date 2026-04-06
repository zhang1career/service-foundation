"""
Add text view: accept raw text, create batch, split into sentences, save to knowledge table.
"""
import logging

from rest_framework.views import APIView

from app_know.consts import SOURCE_TYPE_INSTANT
from app_know.repos.batch_repo import create_batch
from app_know.services.parser_agent import parse_and_store
from common.consts.response_const import RET_INVALID_PARAM, RET_MISSING_PARAM
from common.utils.http_util import resp_ok, resp_err, resp_exception

logger = logging.getLogger(__name__)

MAX_CONTENT_LEN = 500 * 1024  # 500KB


class AddTextKnowledgeView(APIView):
    """POST: add raw text as a new batch. Splits into sentences, saves each to knowledge table."""

    def post(self, request, *args, **kwargs):
        """
        Body: { content: string (required) }
        Returns: { id: batch_id, title, sentence_count, sentences }
        """
        try:
            data = getattr(request, "data", None) or request.POST or {}
            content = (data.get("content") or "").strip()
            if not content:
                return resp_err(code=RET_MISSING_PARAM, message="content is required")
            if len(content) > MAX_CONTENT_LEN:
                return resp_err(
                    code=RET_INVALID_PARAM,
                    message=f"content too long (max {MAX_CONTENT_LEN // 1024}KB)"
                )

            title = (content[:80] + "...") if len(content) > 80 else content
            batch_record = create_batch(title=title, source_type=SOURCE_TYPE_INSTANT, filename=None)
            batch_id = batch_record.id

            sentences = parse_and_store(
                batch_id=batch_id,
                content=content,
                use_ai_classify=True,
                write_sentence_raw=True,
            )

            return resp_ok({
                "id": batch_id,
                "title": title,
                "sentence_count": len(sentences),
                "sentences": sentences,
            })
        except ValueError as e:
            logger.warning("[AddTextKnowledgeView] Validation error: %s", e)
            return resp_err(code=RET_INVALID_PARAM, message=str(e))
        except Exception as e:
            logger.exception("[AddTextKnowledgeView] Error: %s", e)
            return resp_exception(e)
