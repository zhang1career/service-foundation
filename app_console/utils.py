"""app_console 通用工具。"""
from django.urls import reverse
from typing import Any, Dict


def get_edit_return_context(
    list_url_name: str,
    list_label: str = "返回列表",
) -> Dict[str, Any]:
    """编辑页统一返回到列表页。"""
    url = reverse(list_url_name)
    return {"edit_cancel_url": url, "edit_back_label": list_label}
