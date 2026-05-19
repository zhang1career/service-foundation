"""文本风控（app_textmod）：词库管理、词条导入、发布与 API 试调。"""
from __future__ import annotations

import json

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView

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


class TextmodLexiconListView(_TextmodConsoleMixin, TemplateView):
    """词库列表与创建。"""

    template_name = "console/textmod/lexicon_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rows = list_lexicons()
        ctx["lexicon_biz_type_choices"] = lexicon_biz_type_choices_for_template()
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
        return ctx

    def post(self, request, *args, **kwargs):
        if (request.POST.get("action") or "").strip() != "create":
            return HttpResponseRedirect(request.path)
        try:
            create_lexicon(
                name=str(request.POST.get("name", "")),
                biz_type=coerce_lexicon_biz_type_id(request.POST.get("biz_type")),
            )
        except ValueError:
            pass
        return HttpResponseRedirect(request.path)


class TextmodLexiconDetailView(_TextmodConsoleMixin, TemplateView):
    """词库详情：词条列表、批量导入、发布快照。"""

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
        ctx["flash_published"] = (req.GET.get("published") == "1")
        ctx["flash_imported"] = (req.GET.get("imported") == "1")
        ctx["entries_example_json"] = json.dumps(
            [
                {
                    "word": "示例敏感词",
                    "label_id": 1,
                    "suggestion": int(TextmodSuggestionEnum.BLOCK),
                    "priority": 10,
                    "enabled": True,
                }
            ],
            ensure_ascii=False,
            indent=2,
        )
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
            if action == "add_entries":
                raw = (request.POST.get("entries_json") or "").strip()
                rows = json.loads(raw)
                if not isinstance(rows, list):
                    raise ValueError("entries_json 必须是 JSON 数组")
                add_entries(
                    lexicon_id=lid,
                    entries=rows,
                    batch_max=int(settings.TEXTMOD_ENTRY_BATCH_MAX),
                )
                return HttpResponseRedirect(request.path + "?imported=1")
        except json.JSONDecodeError as exc:
            ctx["entries_json_body"] = (request.POST.get("entries_json") or "").strip()
            ctx["form_error"] = f"JSON 解析失败: {exc}"
            return self.render_to_response(ctx)
        except (TypeError, ValueError) as exc:
            ctx["entries_json_body"] = (request.POST.get("entries_json") or "").strip()
            ctx["form_error"] = str(exc)
            return self.render_to_response(ctx)
        return HttpResponseRedirect(request.path)


class TextmodApiConsoleView(_TextmodConsoleMixin, TemplateView):
    """调用 /api/textmod 的浏览器调试页。"""

    template_name = "console/textmod/api_debug.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["textmod_api_base"] = "/api/textmod"
        ctx["textmod_enabled"] = bool(getattr(settings, "APP_TEXTMOD_ENABLED", False))
        lexicons = list_lexicons()
        default_id = int(lexicons[0].id) if lexicons else 1
        ctx["scan_example"] = json.dumps(
            {"text": "待检测文本", "lexicon_id": default_id, "include_normalized": False},
            ensure_ascii=False,
            indent=2,
        )
        return ctx
