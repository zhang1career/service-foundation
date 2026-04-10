"""校验中心：调用方、校验码（verify_code）、校验日志（verify_log）。"""
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

from app_verify.enums import VerifyLevelEnum, VerifyLogActionEnum
from common.enums.service_reg_status_enum import ServiceRegStatus
from app_verify.repos import (
    delete_verify_code_by_id,
    delete_verify_codes_by_ids,
    delete_verify_log_by_id,
    delete_verify_logs_by_ids,
    get_verify_code_by_id,
    get_verify_log_by_id,
    list_verify_codes_page,
    list_verify_logs_page,
)
from app_verify.services.reg_service import RegService as VerifyRegService
from app_verify.services.verify_service import VerifyService

from common.utils.page_util import slice_window_for_page

from app_console.utils import format_epoch_ms_for_display, mask_verify_code_for_display
from app_console.views.reg_console_view import VerifyRegConsoleView


class _VerifyConsoleMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "APP_VERIFY_ENABLED", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


def _verify_reg_label_map() -> dict[int, str]:
    out: dict[int, str] = {}
    try:
        for r in VerifyRegService.list_all():
            rid = int(r["id"])
            name = (r.get("name") or "").strip()
            out[rid] = name if name else f"#{rid}"
    except Exception:
        pass
    return out


def _verify_level_label(level: int) -> str:
    labels = {
        VerifyLevelEnum.PASS: "通过",
        VerifyLevelEnum.LOW: "低",
        VerifyLevelEnum.MEDIUM: "中",
        VerifyLevelEnum.HIGH: "高",
    }
    try:
        return labels.get(VerifyLevelEnum(int(level)), str(level))
    except (ValueError, TypeError):
        return str(level)


def _verify_log_action_label(action: int) -> str:
    if int(action) == int(VerifyLogActionEnum.CODE_REQUEST):
        return "申请校验码"
    if int(action) == int(VerifyLogActionEnum.CODE_CHECK):
        return "核销校验码"
    return str(action)


def _verify_regs_enabled_for_select() -> list[dict]:
    rows: list[dict] = []
    try:
        for r in VerifyRegService.list_all():
            if int(r.get("status", ServiceRegStatus.DISABLED)) != ServiceRegStatus.ENABLED:
                continue
            rid = int(r["id"])
            name = (r.get("name") or "").strip()
            rows.append({"id": rid, "label": name if name else f"#{rid}"})
    except Exception:
        pass
    return rows


def _verify_level_choice_rows() -> list[dict]:
    return [{"value": int(m.value), "label": _verify_level_label(int(m.value))} for m in VerifyLevelEnum]


class VerifyCallerConsoleView(_VerifyConsoleMixin, VerifyRegConsoleView):
    template_name = "console/verify/caller_list.html"


class VerifyCodeListConsoleView(_VerifyConsoleMixin, TemplateView):
    template_name = "console/verify/code_list.html"
    PAGE_SIZE = 30

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            page = int(self.request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            rows, total, resolved_page = list_verify_codes_page(page, self.PAGE_SIZE)
        except Exception:
            rows, total, resolved_page = [], 0, 1
        _, _, total_pages = slice_window_for_page(total, page, self.PAGE_SIZE)
        reg_map = _verify_reg_label_map()
        codes: list[dict] = []
        for r in rows:
            codes.append(
                {
                    "id": r.id,
                    "reg_id": r.reg_id,
                    "reg_label": reg_map.get(int(r.reg_id), f"#{r.reg_id}"),
                    "ref_id": r.ref_id,
                    "level": r.level,
                    "level_label": _verify_level_label(r.level),
                    "code_masked": mask_verify_code_for_display(r.code),
                    "expires_at_fmt": format_epoch_ms_for_display(r.expires_at),
                    "used_at_fmt": format_epoch_ms_for_display(r.used_at) if r.used_at else "—",
                    "ct_fmt": format_epoch_ms_for_display(r.ct),
                }
            )
        ctx["codes"] = codes
        ctx["page"] = resolved_page
        ctx["total"] = total
        ctx["total_pages"] = total_pages
        ctx["page_size"] = self.PAGE_SIZE
        ctx["has_prev"] = resolved_page > 1
        ctx["has_next"] = resolved_page < total_pages
        ctx["verify_regs_active"] = _verify_regs_enabled_for_select()
        ctx["verify_level_choices"] = _verify_level_choice_rows()
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action == "create":
            try:
                rid = int(request.POST.get("reg_id", 0))
                level = int(request.POST.get("level", 0))
                ref_id = int(request.POST.get("ref_id", 0) or 0)
                if rid > 0:
                    VerifyService.issue_code_for_reg_id(rid, level, ref_id)
            except (ValueError, TypeError):
                pass
            return HttpResponseRedirect(request.path)
        if action == "delete":
            try:
                cid = int(request.POST.get("code_id", 0))
                if cid > 0:
                    delete_verify_code_by_id(cid)
            except (ValueError, TypeError):
                pass
        elif action == "bulk_delete":
            raw = request.POST.getlist("code_ids")
            parsed: list[int] = []
            for x in raw:
                try:
                    v = int(x)
                    if v > 0:
                        parsed.append(v)
                except (TypeError, ValueError):
                    pass
            if parsed:
                delete_verify_codes_by_ids(parsed)
        page_q = (request.POST.get("page") or "").strip()
        if page_q.isdigit() and int(page_q) > 1:
            return HttpResponseRedirect(f"{request.path}?page={int(page_q)}")
        return HttpResponseRedirect(request.path)


class VerifyCodeDetailConsoleView(_VerifyConsoleMixin, TemplateView):
    template_name = "console/verify/code_detail.html"

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        code_id = int(kwargs.get("code_id", 0))
        if action == "verify" and code_id > 0:
            typed = (request.POST.get("check_code") or "").strip()
            row = get_verify_code_by_id(code_id)
            if not row or not VerifyService.code_row_awaits_verification(row):
                return HttpResponseRedirect(f"{request.path}?verify=err")
            if typed:
                try:
                    reg = VerifyRegService.get_one(int(row.reg_id))
                    if int(reg["status"]) != 1:
                        raise ValueError("reg disabled")
                    VerifyService.verify_code(
                        int(code_id),
                        typed,
                        (reg.get("access_key") or "").strip(),
                    )
                    return HttpResponseRedirect(f"{request.path}?verify=ok")
                except ValueError:
                    pass
            return HttpResponseRedirect(f"{request.path}?verify=err")
        if action == "delete" and code_id > 0:
            try:
                delete_verify_code_by_id(code_id)
            except Exception:
                pass
            return HttpResponseRedirect(reverse("console:verify-code-list"))
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        code_id = int(kwargs.get("code_id", 0))
        row = get_verify_code_by_id(code_id)
        if row is None:
            raise Http404()
        reg_map = _verify_reg_label_map()
        ctx["row"] = {
            "id": row.id,
            "reg_id": row.reg_id,
            "reg_label": reg_map.get(int(row.reg_id), f"#{row.reg_id}"),
            "ref_id": row.ref_id,
            "level": row.level,
            "level_label": _verify_level_label(row.level),
            "code_masked": mask_verify_code_for_display(row.code),
            "expires_at_fmt": format_epoch_ms_for_display(row.expires_at),
            "used_at_fmt": format_epoch_ms_for_display(row.used_at) if row.used_at else "—",
            "ct_fmt": format_epoch_ms_for_display(row.ct),
        }
        ctx["show_verify_panel"] = VerifyService.code_row_awaits_verification(row)
        return ctx


class VerifyLogListConsoleView(_VerifyConsoleMixin, TemplateView):
    template_name = "console/verify/history_list.html"
    PAGE_SIZE = 30

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            page = int(self.request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            rows, total, resolved_page = list_verify_logs_page(page, self.PAGE_SIZE)
        except Exception:
            rows, total, resolved_page = [], 0, 1
        _, _, total_pages = slice_window_for_page(total, page, self.PAGE_SIZE)
        reg_map = _verify_reg_label_map()
        logs: list[dict] = []
        for r in rows:
            logs.append(
                {
                    "id": r.id,
                    "reg_id": r.reg_id,
                    "reg_label": reg_map.get(int(r.reg_id), f"#{r.reg_id}" if r.reg_id else "—"),
                    "ref_id": r.ref_id,
                    "code_id": r.code_id,
                    "level": r.level,
                    "level_label": _verify_level_label(r.level),
                    "action": r.action,
                    "action_label": _verify_log_action_label(r.action),
                    "ok": r.ok,
                    "ok_label": "成功" if int(r.ok) == 1 else "失败",
                    "message": (r.message or "").strip(),
                    "ct_fmt": format_epoch_ms_for_display(r.ct),
                }
            )
        ctx["logs"] = logs
        ctx["page"] = resolved_page
        ctx["total"] = total
        ctx["total_pages"] = total_pages
        ctx["page_size"] = self.PAGE_SIZE
        ctx["has_prev"] = resolved_page > 1
        ctx["has_next"] = resolved_page < total_pages
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action == "delete":
            try:
                lid = int(request.POST.get("log_id", 0))
                if lid > 0:
                    delete_verify_log_by_id(lid)
            except (ValueError, TypeError):
                pass
        elif action == "bulk_delete":
            raw = request.POST.getlist("log_ids")
            parsed: list[int] = []
            for x in raw:
                try:
                    v = int(x)
                    if v > 0:
                        parsed.append(v)
                except (TypeError, ValueError):
                    pass
            if parsed:
                delete_verify_logs_by_ids(parsed)
        page_q = (request.POST.get("page") or "").strip()
        if page_q.isdigit() and int(page_q) > 1:
            return HttpResponseRedirect(f"{request.path}?page={int(page_q)}")
        return HttpResponseRedirect(request.path)


class VerifyLogDetailConsoleView(_VerifyConsoleMixin, TemplateView):
    template_name = "console/verify/history_detail.html"

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        log_id = int(kwargs.get("log_id", 0))
        if action == "delete" and log_id > 0:
            try:
                delete_verify_log_by_id(log_id)
            except Exception:
                pass
            return HttpResponseRedirect(reverse("console:verify-history-list"))
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        log_id = int(kwargs.get("log_id", 0))
        row = get_verify_log_by_id(log_id)
        if row is None:
            raise Http404()
        reg_map = _verify_reg_label_map()
        ctx["row"] = {
            "id": row.id,
            "reg_id": row.reg_id,
            "reg_label": reg_map.get(int(row.reg_id), f"#{row.reg_id}" if row.reg_id else "—"),
            "ref_id": row.ref_id,
            "code_id": row.code_id,
            "level": row.level,
            "level_label": _verify_level_label(row.level),
            "action": row.action,
            "action_label": _verify_log_action_label(row.action),
            "ok": row.ok,
            "ok_label": "成功" if int(row.ok) == 1 else "失败",
            "message": (row.message or "").strip() or "—",
            "ct_fmt": format_epoch_ms_for_display(row.ct),
        }
        return ctx
