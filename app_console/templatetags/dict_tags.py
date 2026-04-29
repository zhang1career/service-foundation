"""Template filters for dict_catalog labels."""

from django import template

from common.dict_catalog import dict_value_to_label

register = template.Library()


@register.filter
def dict_label(value, code: str) -> str:
    return dict_value_to_label((code or "").strip(), value)
