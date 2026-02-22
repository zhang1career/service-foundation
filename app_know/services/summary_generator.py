"""
Python-based knowledge summary generation from title/description/content. Generated.
Rule-based implementation; can be extended with LLM or external API later.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Max length for generated summary (chars)
SUMMARY_MAX_LEN = 2000


def generate_summary(
    title: str,
    description: Optional[str] = None,
    content: Optional[str] = None,
    source_type: Optional[str] = None,
    max_length: int = SUMMARY_MAX_LEN,
) -> str:
    """
    Generate a short summary from title, description, and optional content.
    Inputs are concatenated and truncated to max_length. Validates inputs.
    Raises ValueError if title is missing or invalid, or max_length invalid.
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
    parts = [f"Title: {title}"]
    if desc:
        parts.append(f"Description: {desc}")
    if cnt:
        parts.append(f"Content: {cnt}")
    if st:
        parts.append(f"(Source: {st})")
    summary = " ".join(parts)
    if len(summary) > max_length:
        summary = summary[: max_length - 3].rstrip() + "..."
    return summary
