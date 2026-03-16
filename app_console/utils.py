"""
app_console 通用工具：如编辑页「按来源区分取消/返回」等。
"""
from django.urls import reverse
from typing import Any, Dict, Optional


def get_edit_return_context(
    request,
    list_url_name: str,
    list_label: str = "返回列表",
    detail_url_name: Optional[str] = None,
    detail_url_kwargs: Optional[Dict[str, Any]] = None,
    detail_label: str = "返回详情",
    from_param: str = "from",
) -> Dict[str, Any]:
    """
    按来源区分「取消」/顶部返回的 URL 和文案，供编辑类页面复用。

    约定：从「详情页」进入编辑时链接带 ?from=detail，从「列表页」进入则不带（或 from=list）。
    本函数根据 request.GET 的 from 参数决定返回目标。

    :param request: HttpRequest（含 GET）
    :param list_url_name: 列表页的 URL name（如 'console:know-batch-list'）
    :param list_label: 回到列表时的链接文案
    :param detail_url_name: 详情页的 URL name（如 'console:know-batch-detail'），可选
    :param detail_url_kwargs: 详情页 reverse 所需 kwargs（如 {'entity_id': 71}），可选
    :param detail_label: 回到详情时的链接文案
    :param from_param: GET 参数名，默认 'from'，值为 'detail' 时回详情
    :return: {'edit_cancel_url': str, 'edit_back_label': str}
    """
    from_detail = (request.GET.get(from_param) or "").strip().lower() == "detail"
    if from_detail and detail_url_name and detail_url_kwargs:
        url = reverse(detail_url_name, kwargs=detail_url_kwargs)
        return {"edit_cancel_url": url, "edit_back_label": detail_label}
    url = reverse(list_url_name)
    return {"edit_cancel_url": url, "edit_back_label": list_label}
