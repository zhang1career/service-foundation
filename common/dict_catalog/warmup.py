"""Prime ``get_dict_by_codes`` LRU after all dict registrations are loaded."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def prime_http_dict_cache() -> None:
    """
    Resolve configured ``codes`` strings once so the first real HTTP request hits
    ``lru_cache`` (see ``get_dict_by_codes``).

    Call from the last app(s) that load ``dict_registration`` (e.g. ``app_verify``).
    """
    from common.dict_catalog.registry import get_dict_by_codes
    from common.utils.django_util import setting_str

    raw = setting_str("DICT_HTTP_PRIME_CODES", "aibroker_nested_param_type")
    for part in str(raw).split(","):
        codes = part.strip()
        if not codes:
            continue
        try:
            get_dict_by_codes(codes)
        except Exception:
            logger.exception("[prime_http_dict_cache] failed for codes=%r", codes)
