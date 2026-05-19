"""文本风控（app_textmod）：控制台词库管理与文件批量导入。"""
from __future__ import annotations

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
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
    get_lexicon,
    list_entries_for_lexicon,
    list_lexicons,
)
from app_textmod.services.lexicon_publish_service import LexiconPublishService


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
        label_id = int((request.POST.get("default_label_id") or "1").strip(), 10)
    except ValueError as exc:
        raise ValueError("label_id 默认值为无效整数") from exc
    try:
        suggestion = int((request.POST.get("default_suggestion") or "").strip(), 10)
    except ValueError as exc:
        raise ValueError("suggestion 默认值为无效整数") from exc
    if suggestion not in (int(TextmodSuggestionEnum.PASS), int(TextmodSuggestionEnum.REVIEW), int(TextmodSuggestionEnum.BLOCK)):
        raise ValueError("suggestion 需为 0(pass)、1(review) 或 2(block)")
    try:
        priority = int((request.POST.get("default_priority") or "10").strip(), 10)
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


class TextmodLexiconListView(_TextmodConsoleMixin, TemplateView):
    """词库列表、创建与批量导入。"""

    template_name = "console/textmod/lexicon_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = list_lexicons()
        ctx["lexicon_biz_type_choices"] = lexicon_biz_type_choices_for_template()
        ctx["import_suggestion_choices"] = _import_suggestion_choices_for_template()
        ctx["batch_max"] = _batch_max()
        ctx["lexicon_rows"] = [
            {
                "id": int(r.id),
                "name": r.name,
                "biz_type": int(r.biz_type),
                "biz_type_label": lexicon_biz_type_label_zh(int(r.biz_type)),
                "ut_fmt": format_epoch_ms_for_display(r.ut),
            }
            for r in rows
        ]
        ctx["flash_imported"] = self.request.GET.get("imported") == "1"
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action == "create":
            try:
                create_lexicon(
                    name=str(request.POST.get("name", "")),
                    biz_type=coerce_lexicon_biz_type_id(request.POST.get("biz_type")),
                )
            except ValueError:
                pass
            return HttpResponseRedirect(request.path)
        if action == "file_import":
            ctx = self.get_context_data(**kwargs)
            lid_raw = (request.POST.get("lexicon_id") or "").strip()
            try:
                lid = int(lid_raw, 10)
            except ValueError:
                ctx["form_error"] = "请选择目标词库"
                return self.render_to_response(ctx)
            if get_lexicon(lid) is None:
                ctx["form_error"] = "词库不存在"
                return self.render_to_response(ctx)
            up = request.FILES.get("import_file")
            if not up:
                ctx["form_error"] = "请选择要上传的 .txt 或 .csv 文件"
                return self.render_to_response(ctx)
            try:
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
            except ValueError as exc:
                ctx["form_error"] = str(exc)
                return self.render_to_response(ctx)
            return HttpResponseRedirect(request.path + "?imported=1")
        return HttpResponseRedirect(request.path)


class TextmodLexiconDetailView(_TextmodConsoleMixin, TemplateView):
    """词库详情：词条列表、文件批量导入、发布快照。"""

    template_name = "console/textmod/lexicon_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lid = int(kwargs["lexicon_id"])
        lex = get_lexicon(lid)
        if lex is None:
            raise Http404()
        ctx["lexicon"] = lex
        suggestion_labels = {
            int(TextmodSuggestionEnum.PASS): "pass",
            int(TextmodSuggestionEnum.REVIEW): "review",
            int(TextmodSuggestionEnum.BLOCK): "block",
        }
        ctx["suggestion_labels"] = suggestion_labels
        ctx["import_suggestion_choices"] = _import_suggestion_choices_for_template()
        ctx["batch_max"] = _batch_max()
        entries = list_entries_for_lexicon(lid, limit=400)
        ctx["entry_rows"] = [
            {
                "id": int(e.id),
                "word": e.word,
                "label_id": int(e.label_id),
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
        ctx["flash_published"] = req.GET.get("published") == "1"
        ctx["flash_imported"] = req.GET.get("imported") == "1"
        return ctx

    def post(self, request, *args, **kwargs):
        lid = int(kwargs["lexicon_id"])
        if get_lexicon(lid) is None:
            raise Http404()
        action = (request.POST.get("action") or "").strip()
        ctx = self.get_context_data(**kwargs)
        try:
            if action == "publish":
                LexiconPublishService.publish(lid)
                return HttpResponseRedirect(request.path + "?published=1")
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
                return HttpResponseRedirect(request.path + "?imported=1")
        except ValueError as exc:
            ctx["form_error"] = str(exc)
            return self.render_to_response(ctx)
        return HttpResponseRedirect(request.path)
