"""app_console 通用工具。"""
import json
from datetime import datetime, timezone as dt_timezone
from typing import Any, Dict

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone as dj_timezone
from django.utils.safestring import mark_safe

# 与 django.utils.html.json_script 一致；整段 JSON 不经过 str.format，避免入参 spec 含大量 { }（如 object_array）时与占位符解析冲突。
_JSON_SCRIPT_ESCAPES = {ord(">"): "\\u003E", ord("<"): "\\u003C", ord("&"): "\\u0026"}


def embed_dict_as_json_script_body(data: dict):
    """供 <script type="application/json"> 正文使用：序列化并做 script 安全转义，返回 mark_safe 字符串。"""
    if not isinstance(data, dict):
        data = {}
    out: dict[str, str] = {}
    for k, v in data.items():
        sk = str(k)
        if v is None:
            out[sk] = ""
        elif isinstance(v, memoryview):
            out[sk] = v.tobytes().decode("utf-8", errors="replace")
        elif isinstance(v, (bytes, bytearray)):
            out[sk] = bytes(v).decode("utf-8", errors="replace")
        elif isinstance(v, str):
            out[sk] = v
        else:
            out[sk] = str(v)
    raw = json.dumps(out, cls=DjangoJSONEncoder).translate(_JSON_SCRIPT_ESCAPES)
    return mark_safe(raw)


def format_epoch_ms_for_display(ms) -> str:
    """Unix 毫秒时间戳 → 本地墙钟时间字符串（遵循 settings.TIME_ZONE，默认东八区）。"""
    if ms is None:
        return "-"
    try:
        iv = int(ms)
    except (TypeError, ValueError):
        return "-"
    if iv <= 0:
        return "-"
    aware_utc = datetime.fromtimestamp(iv / 1000.0, tz=dt_timezone.utc)
    local = dj_timezone.localtime(aware_utc)
    return local.strftime("%Y-%m-%d %H:%M:%S")


def get_edit_return_context(
    list_url_name: str,
    list_label: str = "返回列表",
) -> Dict[str, Any]:
    """编辑页统一返回到列表页。"""
    url = reverse(list_url_name)
    return {"edit_cancel_url": url, "edit_back_label": list_label}
