from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import QueryDict


def post_like_mapping_to_dict(raw: Any) -> dict[str, Any]:
    """Convert POST-like data to a ``dict`` of scalar values.

    In Django, ``dict(QueryDict)`` binds each key to a *list* of values (see
    ``getlist``). HTML forms should use the last value per key via
    :meth:`django.http.QueryDict.dict`.
    """
    if isinstance(raw, QueryDict):
        return raw.dict()
    if isinstance(raw, dict):
        return dict(raw)
    return dict(raw)


def effective_setting_str(override: str | None, setting_attr: str) -> str:
    """Non-empty stripped override wins; otherwise getattr(settings, attr, '') as str, stripped."""
    if override is not None:
        s = str(override).strip()
        if s:
            return s
    return str(getattr(settings, setting_attr, "")).strip()


def post_to_dict(request):
    """
    Convert post data to dict
    """
    data = {}

    # get param
    for key in request.data.keys():
        data[key] = request.data.get(key)

    return data
