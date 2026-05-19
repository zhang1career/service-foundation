"""文本风控（app_textmod）：控制台词库与词条管理。

页面路由在 ``console/textmod/``；枚举字典与词库 JSON API（含 ``GET .../dict``、lexicons 等）
挂载在 ``/admin/textmod/``（见 ``app_textmod.urls_lexicon_admin``）。公开能力仅为
``/api/textmod/`` 下的 health 与 scan。
"""
from __future__ import annotations

import math
from urllib.parse import parse_qsl, urlencode

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

from app_console.textmod_import_parse import normalize_entries, parse_lexicon_import_bytes
from app_console.utils import format_epoch_ms_for_display
from app_textmod.enums.lexicon_biz_type_enum import (
    coerce_lexicon_biz_type_id,
    lexicon_biz_type_choices_for_template,
    lexicon_biz_type_label_zh,
)
from app_textmod.enums.suggestion_enum import TextmodSuggestionEnum
from app_textmod.repos.lexicon_repo import (
    add_entries,
    create_lexicon,
    create_entry,
    delete_entry,
    get_lexicon,
    get_lexicon_entry,
    list_entries_for_lexicon_page,
    list_lexicons,
    update_entry,
    update_entry_enabled,
)
from app_textmod.services.lexicon_publish_service import LexiconPublishService
from common.dict_catalog import get_dict_by_codes

_ENTRY_PAGE_SIZE = 50
_ENTRY_MAX_PAGE = 200
_ENTRY_QUERY_KEYS = {"word", "label_id", "suggestion", "enabled", "sort_by", "sort_dir", "page"}


class _TextmodConsoleMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "APP_TEXTMOD_ENABLED", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


def _batch_max() -> int:
    return int(settings.TEXTMOD_ENTRY_BATCH_MAX)


def _import_suggestion_choices_for_template():
    return [
        {"value": int(TextmodSuggestionEnum.BLOCK), "label": "block（拦截）"},
        {"value": int(TextmodSuggestionEnum.REVIEW), "label": "review（审核）"},
        {"value": int(TextmodSuggestionEnum.PASS), "label": "pass（放行）"},
    ]


def _read_import_defaults(request) -> tuple[int, int, int, bool]:
    try:
        label_id = int((request.POST.get("default_label_id") or "0").strip(), 10)
    except ValueError as exc:
        raise ValueError("label_id 默认值为无效整数") from exc
    try:
        suggestion = int((request.POST.get("default_suggestion") or "").strip(), 10)
    except ValueError as exc:
        raise ValueError("suggestion 默认值为无效整数") from exc
    if suggestion not in (int(TextmodSuggestionEnum.PASS), int(TextmodSuggestionEnum.REVIEW), int(TextmodSuggestionEnum.BLOCK)):
        raise ValueError("suggestion 需为 0(pass)、1(review) 或 2(block)")
    try:
        priority = int((request.POST.get("default_priority") or "100").strip(), 10)
    except ValueError as exc:
        raise ValueError("priority 默认值为无效整数") from exc
    enabled_raw = (request.POST.get("default_enabled") or "1").strip().lower()
    default_enabled = enabled_raw in ("1", "true", "yes", "on")
    return label_id, suggestion, priority, default_enabled


def _import_entries_with_chunking(*, lexicon_id: int, entries: list[dict]) -> None:
    batch = _batch_max()
    for i in range(0, len(entries), batch):
        chunk = entries[i : i + batch]
        add_entries(lexicon_id=lexicon_id, entries=chunk, batch_max=batch)


def _parse_optional_int(raw: object) -> int | None:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        return int(s, 10)
    except ValueError:
        return None


def _build_dict_value_label_map(dict_code: str) -> dict[int, str]:
    raw = get_dict_by_codes(dict_code).get(dict_code) or []
    out: dict[int, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            value = int(item.get("v"))
        except (TypeError, ValueError):
            continue
        out[value] = str(item.get("k", value))
    return out


def _sanitize_entry_query(raw_query: str) -> str:
    if not raw_query:
        return ""
    pairs = parse_qsl(raw_query, keep_blank_values=False)
    out: list[tuple[str, str]] = []
    for key, value in pairs:
        if key in _ENTRY_QUERY_KEYS:
            out.append((key, value))
    return urlencode(out)


def _compose_query(*, base_query: str, **extra: str | int | None) -> str:
    pairs = parse_qsl(base_query, keep_blank_values=False) if base_query else []
    kv: dict[str, str] = {k: v for k, v in pairs if k in _ENTRY_QUERY_KEYS}
    for key, value in extra.items():
        if value is None:
            kv.pop(key, None)
        else:
            kv[str(key)] = str(value)
    return urlencode(kv)


def _entry_detail_redirect(*, lexicon_id: int, base_query: str, **extra: str | int | None) -> HttpResponseRedirect:
    path = reverse("console:textmod-lexicon-detail", kwargs={"lexicon_id": lexicon_id})
    query = _compose_query(base_query=base_query, **extra)
    if query:
        return HttpResponseRedirect(path + "?" + query)
    return HttpResponseRedirect(path)


def _read_entry_form(request) -> tuple[str, int, int, int, int]:
    word = (request.POST.get("word") or "").strip()
    if not word:
        raise ValueError("word 不能为空")
    try:
        label_id = int((request.POST.get("label_id") or "0").strip(), 10)
        suggestion = int((request.POST.get("suggestion") or "0").strip(), 10)
        priority = int((request.POST.get("priority") or "0").strip(), 10)
    except ValueError as exc:
        raise ValueError("label_id / suggestion / priority 需为整数") from exc
    if suggestion not in (int(TextmodSuggestionEnum.PASS), int(TextmodSuggestionEnum.REVIEW), int(TextmodSuggestionEnum.BLOCK)):
        raise ValueError("suggestion 需为 0(pass)、1(review) 或 2(block)")
    enabled = 1 if (request.POST.get("enabled") or "1").strip() in ("1", "true", "yes", "on") else 0
    return word, label_id, suggestion, priority, enabled


class TextmodLexiconListView(_TextmodConsoleMixin, TemplateView):
    """词库列表、创建与发布。"""

    template_name = "console/textmod/lexicon_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = list_lexicons()
        ctx["lexicon_biz_type_choices"] = lexicon_biz_type_choices_for_template()
        ctx["lexicon_rows"] = [
            {
                "id": int(r.id),
                "name": r.name,
                "biz_type_label": lexicon_biz_type_label_zh(int(r.biz_type)),
                "ut_fmt": format_epoch_ms_for_display(r.ut),
            }
            for r in rows
        ]
        req = self.request
        ctx["flash_published"] = req.GET.get("published") == "1"
        ctx["flash_created"] = req.GET.get("created") == "1"
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action == "create":
            created = False
            try:
                create_lexicon(
                    name=str(request.POST.get("name", "")),
                    biz_type=coerce_lexicon_biz_type_id(request.POST.get("biz_type")),
                )
                created = True
            except ValueError:
                pass
            if created:
                return HttpResponseRedirect(request.path + "?created=1")
            return HttpResponseRedirect(request.path)
        if action == "publish":
            published = False
            try:
                lexicon_id = int((request.POST.get("lexicon_id") or "").strip(), 10)
                if get_lexicon(lexicon_id) is not None:
                    LexiconPublishService.publish(lexicon_id)
                    published = True
            except ValueError:
                pass
            if published:
                return HttpResponseRedirect(request.path + "?published=1")
            return HttpResponseRedirect(request.path)
        return HttpResponseRedirect(request.path)


class TextmodLexiconDetailView(_TextmodConsoleMixin, TemplateView):
    """词库详情：词条列表、词条维护与文件批量导入。"""

    template_name = "console/textmod/lexicon_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lid = int(kwargs["lexicon_id"])
        lex = get_lexicon(lid)
        if lex is None:
            raise Http404()
        ctx["lexicon"] = lex
        label_labels = _build_dict_value_label_map("textmod_label")
        suggestion_labels = _build_dict_value_label_map("textmod_suggestion")
        ctx["suggestion_labels"] = suggestion_labels
        ctx["import_suggestion_choices"] = _import_suggestion_choices_for_template()
        ctx["batch_max"] = _batch_max()
        raw_word = (self.request.GET.get("word") or "").strip()
        raw_sort_by = (self.request.GET.get("sort_by") or "ct").strip()
        raw_sort_dir = (self.request.GET.get("sort_dir") or "desc").strip()
        raw_page = (self.request.GET.get("page") or "1").strip()
        page = int(raw_page) if raw_page.isdigit() else 1
        if page < 1:
            page = 1
        if page > _ENTRY_MAX_PAGE:
            page = _ENTRY_MAX_PAGE
            ctx["page_cap_reached"] = True
        else:
            ctx["page_cap_reached"] = False
        label_id = _parse_optional_int(self.request.GET.get("label_id"))
        suggestion = _parse_optional_int(self.request.GET.get("suggestion"))
        enabled = _parse_optional_int(self.request.GET.get("enabled"))
        sort_by = "priority" if raw_sort_by == "priority" else "ct"
        sort_dir = "asc" if raw_sort_dir == "asc" else "desc"
        total, entries = list_entries_for_lexicon_page(
            lexicon_id=lid,
            page=page,
            page_size=_ENTRY_PAGE_SIZE,
            word=raw_word or None,
            label_id=label_id,
            suggestion=suggestion,
            enabled=enabled,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        ctx["entry_rows"] = [
            {
                "id": int(e.id),
                "word": e.word,
                "label_id": int(e.label_id),
                "label_id_label": label_labels.get(int(e.label_id), str(int(e.label_id))),
                "suggestion": int(e.suggestion),
                "suggestion_label": suggestion_labels.get(int(e.suggestion), str(int(e.suggestion))),
                "priority": int(e.priority),
                "enabled": int(e.enabled),
                "ct_fmt": format_epoch_ms_for_display(e.ct),
            }
            for e in entries
        ]
        ctx["lexicon_biz_type_label"] = lexicon_biz_type_label_zh(int(lex.biz_type))
        req = self.request
        ctx["flash_imported"] = req.GET.get("imported") == "1"
        ctx["flash_need_publish"] = req.GET.get("changed") == "1"
        ctx["entry_total"] = int(total)
        ctx["entry_page"] = int(page)
        ctx["entry_page_size"] = int(_ENTRY_PAGE_SIZE)
        ctx["entry_total_pages"] = max(1, math.ceil(total / _ENTRY_PAGE_SIZE) if total else 1)
        ctx["filter_word"] = raw_word
        ctx["filter_label_id"] = label_id
        ctx["filter_suggestion"] = suggestion
        ctx["filter_enabled"] = enabled
        ctx["sort_by"] = sort_by
        ctx["sort_dir"] = sort_dir
        query_base = _compose_query(
            base_query="",
            word=raw_word or None,
            label_id=label_id,
            suggestion=suggestion,
            enabled=enabled,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=None,
        )
        current_query = _sanitize_entry_query(req.GET.urlencode())
        ctx["entry_query_base"] = query_base
        ctx["entry_current_query"] = current_query
        return ctx

    def post(self, request, *args, **kwargs):
        lid = int(kwargs["lexicon_id"])
        if get_lexicon(lid) is None:
            raise Http404()
        action = (request.POST.get("action") or "").strip()
        next_query = _sanitize_entry_query((request.POST.get("next_query") or "").strip())
        ctx = self.get_context_data(**kwargs)
        try:
            if action == "file_import":
                up = request.FILES.get("import_file")
                if not up:
                    ctx["form_error"] = "请选择要上传的 .txt 或 .csv 文件"
                    return self.render_to_response(ctx)
                raw = up.read()
                defaults = _read_import_defaults(request)
                parsed = parse_lexicon_import_bytes(raw=raw, filename=getattr(up, "name", "") or "")
                entries = normalize_entries(
                    parsed,
                    default_label_id=defaults[0],
                    default_suggestion=defaults[1],
                    default_priority=defaults[2],
                    default_enabled=defaults[3],
                )
                _import_entries_with_chunking(lexicon_id=lid, entries=entries)
                return _entry_detail_redirect(
                    lexicon_id=lid,
                    base_query=next_query,
                    imported=1,
                    changed=1,
                )
            if action == "entry_create":
                word, label_id, suggestion, priority, enabled = _read_entry_form(request)
                create_entry(
                    lexicon_id=lid,
                    word=word,
                    label_id=label_id,
                    suggestion=suggestion,
                    priority=priority,
                    enabled=enabled,
                )
                return _entry_detail_redirect(lexicon_id=lid, base_query=next_query, changed=1)
            if action == "entry_update":
                entry_id = int((request.POST.get("entry_id") or "").strip(), 10)
                word, label_id, suggestion, priority, enabled = _read_entry_form(request)
                update_entry(
                    lexicon_id=lid,
                    entry_id=entry_id,
                    word=word,
                    label_id=label_id,
                    suggestion=suggestion,
                    priority=priority,
                    enabled=enabled,
                )
                return _entry_detail_redirect(lexicon_id=lid, base_query=next_query, changed=1)
            if action == "entry_delete":
                entry_id = int((request.POST.get("entry_id") or "").strip(), 10)
                delete_entry(lexicon_id=lid, entry_id=entry_id)
                return _entry_detail_redirect(lexicon_id=lid, base_query=next_query, changed=1)
            if action == "entry_toggle_enabled":
                entry_id = int((request.POST.get("entry_id") or "").strip(), 10)
                enabled_raw = (request.POST.get("enabled") or "").strip()
                if enabled_raw not in {"0", "1"}:
                    raise ValueError("enabled 需为 0 或 1")
                update_entry_enabled(
                    lexicon_id=lid,
                    entry_id=entry_id,
                    enabled=int(enabled_raw),
                )
                return _entry_detail_redirect(lexicon_id=lid, base_query=next_query, changed=1)
        except ValueError as exc:
            ctx["form_error"] = str(exc)
            return self.render_to_response(ctx)
        return _entry_detail_redirect(lexicon_id=lid, base_query=next_query)


class TextmodLexiconEntryDetailView(_TextmodConsoleMixin, TemplateView):
    """词条详情页。"""

    template_name = "console/textmod/lexicon_entry_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lid = int(kwargs["lexicon_id"])
        entry_id = int(kwargs["entry_id"])
        lex = get_lexicon(lid)
        if lex is None:
            raise Http404()
        entry = get_lexicon_entry(lexicon_id=lid, entry_id=entry_id)
        if entry is None:
            raise Http404()
        suggestion_labels = {
            int(TextmodSuggestionEnum.PASS): "pass",
            int(TextmodSuggestionEnum.REVIEW): "review",
            int(TextmodSuggestionEnum.BLOCK): "block",
        }
        back_query = _sanitize_entry_query((self.request.GET.get("next_query") or "").strip())
        back_url = reverse("console:textmod-lexicon-detail", kwargs={"lexicon_id": lid})
        if back_query:
            back_url = back_url + "?" + back_query
        ctx["lexicon"] = lex
        ctx["entry"] = entry
        ctx["entry_suggestion_label"] = suggestion_labels.get(int(entry.suggestion), str(int(entry.suggestion)))
        ctx["entry_ct_fmt"] = format_epoch_ms_for_display(int(entry.ct))
        ctx["lexicon_biz_type_label"] = lexicon_biz_type_label_zh(int(lex.biz_type))
        ctx["back_url"] = back_url
        return ctx
