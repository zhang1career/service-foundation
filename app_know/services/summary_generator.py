"""
Python-based knowledge summary generation from title/description/content.
Supports rule-based generation and AI-powered generation via AigcBestAPI.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Max length for generated summary (chars)
SUMMARY_MAX_LEN = 2000

# AI generation prompt template
SUMMARY_PROMPT_TEMPLATE = """Please generate a concise summary for the following knowledge item.
The summary should capture the key points and main ideas in 2-3 sentences.

Title: {title}
{description_section}
{content_section}
{source_section}

Summary:"""


def _get_ai_client():
    """Get AigcBestAPI client lazily, only when needed."""
    try:
        from common.apis.aigcbest_api import AigcBestAPI
    except ImportError:
        logger.warning("[summary_generator] AigcBestAPI not available")
        return None

    base_url = os.environ.get("AIGC_API_URL", "https://api2.aigcbest.top/v1")
    api_key = os.environ.get("AIGC_API_KEY", "")
    model = os.environ.get("AIGC_API_MODEL", "gpt-4o-mini")

    if not api_key:
        logger.warning("[summary_generator] AIGC_API_KEY not configured")
        return None

    try:
        return AigcBestAPI(base_url, api_key, model)
    except Exception as e:
        logger.exception("[summary_generator] Failed to create AigcBestAPI client: %s", e)
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
        content: Optional content/metadata
        source_type: Optional source type
        max_length: Maximum length of generated summary
        use_ai: If True, use AigcBestAPI for AI-powered generation; falls back to rule-based if AI fails

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
    """Generate summary using AigcBestAPI. Returns None on failure."""
    client = _get_ai_client()
    if client is None:
        return None

    description_section = f"Description: {description}" if description else ""
    content_section = f"Content: {content[:1000]}..." if content and len(content) > 1000 else (f"Content: {content}" if content else "")
    source_section = f"Source Type: {source_type}" if source_type else ""

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        title=title,
        description_section=description_section,
        content_section=content_section,
        source_section=source_section,
    )

    try:
        result = client.chat(prompt, temperature=0.3)
        if result:
            summary = result.strip()
            if len(summary) > max_length:
                summary = summary[: max_length - 3].rstrip() + "..."
            return summary
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
