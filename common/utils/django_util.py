from __future__ import annotations

from django.conf import settings


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
