from django import template

from app_cms.support.console_form_value import attribute_for_field

register = template.Library()


@register.simple_tag
def cms_field_value(model, field_def: dict):
    name = field_def.get("name") or ""
    ftype = field_def.get("type") or "string"
    return attribute_for_field(model, str(name), str(ftype))


@register.filter
def post_get(post, key: str) -> str:
    if not post or not key:
        return ""
    v = post.get(key)
    return "" if v is None else v


@register.filter
def dict_get(mapping, key):
    if not isinstance(mapping, dict):
        return ""
    if key is None:
        return ""
    v = mapping.get(key)
    return "" if v is None else v
