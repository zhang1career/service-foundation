"""CloudFront-style list pagination utilities."""
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar("T")


def build_cloudfront_list_response(
    items: List[T],
    max_items: int,
    marker_getter: Callable[[T], str],
) -> Dict[str, Any]:
    """
    Build CloudFront-style list response with pagination.

    Args:
        items: Raw list from query (may include one extra item for truncation check)
        max_items: Maximum items per page
        marker_getter: Callable to extract marker string from the last item

    Returns:
        Dict with keys: Items, Quantity, NextMarker, IsTruncated
    """
    is_truncated = len(items) > max_items
    if is_truncated:
        items = items[:max_items]
    next_marker = marker_getter(items[-1]) if is_truncated and items else None
    return {
        "Items": items,
        "Quantity": len(items),
        "NextMarker": next_marker,
        "IsTruncated": is_truncated,
    }
