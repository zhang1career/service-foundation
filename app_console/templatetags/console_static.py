"""Template tags for app_console static assets with cache busting."""
import os

from django import template
from django.templatetags.static import static
from django.contrib.staticfiles.finders import find

register = template.Library()


@register.simple_tag(takes_context=True)
def static_ver(context, path):
    """
    Return static URL with global version query for cache busting.
    Version comes from context['static_version'] (set by console_context, timestamp at process start).
    Usage: {% static_ver 'console/css/style.css' %}
    """
    url = static(path)
    version = context.get("static_version")
    if version is not None:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}v={version}"
    return url


@register.simple_tag
def static_mtime(path):
    """
    Return static URL with file modification time as cache buster.
    Usage: {% static_mtime 'console/js/list-actions.js' %}
    """
    url = static(path)
    found = find(path)
    if found and os.path.exists(found):
        mtime = int(os.path.getmtime(found))
        return f"{url}?v={mtime}"
    return url
