"""Template tags for app_console static assets with cache busting."""
from django import template
from django.templatetags.static import static
from django.contrib.staticfiles.finders import find
import os

register = template.Library()


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
