from __future__ import annotations

from functools import partial
from typing import Any, Callable

from django.conf import settings
from django.db import connection, transaction
from django.db.models import QuerySet
from django.http import QueryDict

_MISSING = object()


def select_for_update_skip_locked(queryset: QuerySet) -> QuerySet:
    """Row lock for concurrent scanners; uses ``SKIP LOCKED`` only if the DB supports it."""
    if getattr(connection.features, "supports_select_for_update_skip_locked", False):
        return queryset.select_for_update(skip_locked=True)
    return queryset.select_for_update()


def schedule_on_commit(func: Callable[..., Any], /, *args, **kwargs) -> None:
    """Run ``func(*args, **kwargs)`` after the current DB transaction commits successfully."""
    transaction.on_commit(partial(func, *args, **kwargs))


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


def setting_str(name: str, default: str) -> str:
    """Django setting *name* as a non-empty string: strip; missing, ``None``, or blank → *default*."""
    raw = getattr(settings, name, _MISSING)
    if raw is _MISSING or raw is None:
        return default
    s = str(raw).strip()
    return s or default


def effective_setting_str(override: str | None, setting_attr: str) -> str:
    """Non-empty stripped *override* wins; else :func:`setting_str` for *setting_attr* with default ``""``."""
    if override is not None:
        s = str(override).strip()
        if s:
            return s
    return setting_str(setting_attr, "")


def post_to_dict(request):
    """
    Convert post data to dict
    """
    data = {}

    # get param
    for key in request.data.keys():
        data[key] = request.data.get(key)

    return data
