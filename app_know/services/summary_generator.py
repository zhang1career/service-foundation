"""
Python-based knowledge summary generation from title/description/content.
Supports rule-based generation and AI-powered generation via TextAI.
"""
import logging
import os
from typing import Optional

from common.consts.string_const import EMPTY_STRING

logger = logging.getLogger(__name__)

# Max length for generated summary (chars)
SUMMARY_MAX_LEN = 2000

# Singleton TextAI instance (lazy initialization)
_text_ai_client = None

SUMMARY_QUESTION = "generate a concise summary capturing the key points and main ideas in 1 sentence, written in English."


def _get_text_ai():
    """Get TextAI client lazily, only when needed."""
    global _text_ai_client
    if _text_ai_client is not None:
        return _text_ai_client

    try:
        from common.services.ai.text_ai import TextAI
    except ImportError:
        logger.warning("[summary_generator] TextAI not available")
        return None

    base_url = os.environ.get("AIGC_API_URL", EMPTY_STRING)
    api_key = os.environ.get("AIGC_API_KEY", EMPTY_STRING)
    model = os.environ.get("AIGC_GPT_MODEL", "gpt-4o-mini")
    if not api_key:
        logger.warning("[summary_generator] AIGC_API_KEY not configured")
        return None

    try:
        _text_ai_client = TextAI(base_url, api_key, model)
        return _text_ai_client
    except Exception as e:
        logger.exception("[summary_generator] Failed to create TextAI client: %s", e)
        return None


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
        use_ai: If True, use TextAI for AI-powered generation; falls back to rule-based if AI fails

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
    """Generate summary using TextAI.ask_and_answer. Returns None on failure."""
    client = _get_text_ai()
    if client is None:
        return None

    if not content:
        raise Exception("content is empty")
    text = content[:1000] + "..." if len(content) > 1000 else content

    try:
        logger.info("[summary_generator] Calling TextAI for title: %s", title[:50])
        prompt, result = client.ask_and_answer(
            text=text,
            role="knowledge summarization",
            question=SUMMARY_QUESTION,
            temperature=0.3
        )
        logger.info("[summary_generator] TextAI prompt: %s", prompt[:200])
        if result and result != "no":
            summary = result.strip()
            logger.info("[summary_generator] TextAI response received, summary length: %d", len(summary))
            logger.info("[summary_generator] Summary: %s", summary[:500])
            if len(summary) > max_length:
                summary = summary[: max_length - 3].rstrip() + "..."
            return summary
        else:
            logger.warning("[summary_generator] TextAI returned empty or 'no' result")
    except Exception as e:
        logger.exception("[summary_generator] AI generation error: %s", e)

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
