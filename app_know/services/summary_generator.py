"""
Python-based knowledge summary generation from title/description/content.
AI path uses app_aibroker over HTTP only (no in-process OpenAI client).
"""
import logging
from typing import Optional

from common.consts.string_const import EMPTY_STRING

logger = logging.getLogger(__name__)

# Max length for generated summary (chars)
SUMMARY_MAX_LEN = 2000

SUMMARY_QUESTION = "generate a concise summary capturing the key points and main ideas in 1 sentence, written in English."


def generate_summary(
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        source_type: Optional[str] = None,
        max_length: int = SUMMARY_MAX_LEN,
        use_ai: bool = False,
) -> str:
    """
    Generate a short summary from title, description, and optional content.

    Args:
        title: Knowledge title (required)
        description: Optional description
        content: Optional content
        source_type: Optional source type
        max_length: Maximum length of generated summary
        use_ai: If True, use app_aibroker for generation; falls back to rule-based if broker fails

    Returns:
        Generated summary string

    Raises:
        ValueError: If title is missing or invalid, or max_length invalid
    """
    if title is None or not isinstance(title, str):
        raise ValueError("title is required and must be a string")
    if max_length is None or not isinstance(max_length, int) or max_length <= 0:
        raise ValueError("max_length must be a positive integer")
    title = title.strip()
    if not title:
        raise ValueError("title cannot be empty")

    desc = (description or "").strip() if isinstance(description, str) else ""
    cnt = (content or "").strip() if isinstance(content, str) else ""
    st = (source_type or "").strip() if isinstance(source_type, str) else ""

    if use_ai:
        ai_summary = _generate_summary_with_ai(title, desc, cnt, st, max_length)
        if ai_summary:
            return ai_summary
        logger.info("[summary_generator] AI generation failed, falling back to rule-based")

    return _generate_summary_rule_based(title, desc, cnt, st, max_length)


def _generate_summary_with_ai(
        title: str,
        description: str,
        content: str,
        source_type: str,
        max_length: int,
) -> Optional[str]:
    """Generate summary via app_aibroker only. Returns None on failure."""
    if not content:
        raise Exception("content is empty")
    text = content[:1000] + "..." if len(content) > 1000 else content

    try:
        from common.services.aibroker_client import aibroker_ask_and_answer

        logger.info("[summary_generator] Calling AIBroker for title: %s", title[:50])
        result = aibroker_ask_and_answer(
            text=text,
            role="knowledge summarization",
            question=SUMMARY_QUESTION,
            additional_question=EMPTY_STRING,
            temperature=0.3,
        )
        logger.info("[summary_generator] AIBroker response received")
        if result and result != "no":
            summary = result.strip()
            if len(summary) > max_length:
                summary = summary[: max_length - 3].rstrip() + "..."
            return summary
        logger.warning("[summary_generator] AIBroker returned empty or 'no' result")
    except Exception as e:
        logger.exception("[summary_generator] AIBroker generation error: %s", e)

    return None


def _generate_summary_rule_based(
        title: str,
        description: str,
        content: str,
        source_type: str,
        max_length: int,
) -> str:
    """Generate summary using rule-based concatenation."""
    parts = [f"Title: {title}"]
    if description:
        parts.append(f"Description: {description}")
    if content:
        parts.append(f"Content: {content}")
    if source_type:
        parts.append(f"(Source: {source_type})")
    summary = " ".join(parts)
    if len(summary) > max_length:
        summary = summary[: max_length - 3].rstrip() + "..."
    return summary
