"""AI Broker 控制台：调用方、提供商/模型、提示模板（直接调用 app_aibroker 服务层）。"""
import json
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone as django_timezone
from django.views.generic import TemplateView

from app_aibroker.services.provider_service import ModelService, ProviderService
from app_aibroker.services.reg_service import RegService as AibrokerRegService
from app_aibroker.services.template_admin_service import TemplateAdminService
from common.dict_catalog import dict_value_to_label, get_dict_by_codes


def _format_prompt_tpl_ms(ms) -> str:
    """将 prompt_tpl.ct / ut（毫秒）格式化为 yyyy-MM-dd HH:mm:ss（尊重 USE_TZ）。"""
    if ms is None:
        return "—"
    try:
        iv = int(ms)
    except (TypeError, ValueError):
        return "—"
    if iv <= 0:
        return "—"
    sec = iv / 1000.0
    if settings.USE_TZ:
        aware = datetime.fromtimestamp(sec, tz=dt_timezone.utc)
        dt = django_timezone.localtime(aware)
    else:
        dt = datetime.fromtimestamp(sec)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _prompt_tpl_name_list(s) -> list[str]:
    """解析 input_variables / output_variables JSON 为有序名称列表（与控制台列表编辑器一致）。"""
    if not s or not str(s).strip():
        return []
    try:
        arr = json.loads(s)
    except json.JSONDecodeError:
        return []
    if not isinstance(arr, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for x in arr:
        if not isinstance(x, dict):
            continue
        n = x.get("name")
        if not isinstance(n, str):
            continue
        n = n.strip()
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out


class _AibrokerConsoleMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "APP_AIBROKER_ENABLED", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


class AibrokerRegConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/reg_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "regs"
        try:
            ctx["regs"] = AibrokerRegService.list_all()
        except Exception:
            ctx["regs"] = []
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                AibrokerRegService.create_by_payload(
                    {
                        "name": (request.POST.get("name") or "").strip(),
                        "status": 1,
                    }
                )
            elif action == "update":
                rid = int(request.POST.get("reg_id", 0))
                AibrokerRegService.update_by_payload(
                    rid,
                    {"name": (request.POST.get("name") or "").strip()},
                )
            elif action == "set_status":
                rid = int(request.POST.get("reg_id", 0))
                st = int(request.POST.get("status", 0))
                AibrokerRegService.update_by_payload(rid, {"status": st})
            elif action == "delete":
                rid = int(request.POST.get("reg_id", 0))
                AibrokerRegService.delete(rid)
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)


class AibrokerProviderConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/providers.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "providers"
        try:
            ctx["providers"] = ProviderService.list_all()
        except Exception:
            ctx["providers"] = []
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                ProviderService.create_by_payload(
                    {
                        "name": (request.POST.get("name") or "").strip(),
                        "base_url": (request.POST.get("base_url") or "").strip(),
                        "api_key": (request.POST.get("api_key") or "").strip(),
                        "status": int(request.POST.get("status", 1)),
                    }
                )
            elif action == "update":
                pid = int(request.POST.get("provider_id", 0))
                payload = {
                    "name": (request.POST.get("name") or "").strip(),
                    "base_url": (request.POST.get("base_url") or "").strip(),
                }
                ak = (request.POST.get("api_key") or "").strip()
                if ak:
                    payload["api_key"] = ak
                ProviderService.update_by_payload(pid, payload)
            elif action == "set_status":
                pid = int(request.POST.get("provider_id", 0))
                st = int(request.POST.get("status", 0))
                ProviderService.update_by_payload(pid, {"status": st})
            elif action == "delete":
                pid = int(request.POST.get("provider_id", 0))
                ProviderService.delete(pid)
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)


class AibrokerModelConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/models.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "models"
        pid = int(kwargs.get("provider_id", 0))
        ctx["provider_id"] = pid
        ctx["provider"] = None
        ctx["models"] = []
        try:
            p = ProviderService.get_one(pid)
            ctx["provider"] = p
            ctx["models"] = ModelService.list_for_provider(pid)
        except ValueError:
            pass
        except Exception:
            pass
        return ctx

    def post(self, request, *args, **kwargs):
        provider_id = int(kwargs.get("provider_id", 0))
        try:
            ProviderService.get_one(provider_id)
        except ValueError:
            return HttpResponseRedirect(request.path)
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                ModelService.create_by_payload(
                    {
                        "provider_id": provider_id,
                        "model_name": (request.POST.get("model_name") or "").strip(),
                        "capability": int(request.POST.get("capability", 0)),
                        "status": int(request.POST.get("status", 1)),
                    }
                )
            elif action == "update":
                mid = int(request.POST.get("model_id", 0))
                ModelService.update(
                    mid,
                    {
                        "model_name": (request.POST.get("model_name") or "").strip(),
                        "capability": int(request.POST.get("capability", 0)),
                        "status": int(request.POST.get("status", 1)),
                    },
                )
            elif action == "set_status":
                mid = int(request.POST.get("model_id", 0))
                st = int(request.POST.get("status", 0))
                ModelService.update(mid, {"status": st})
            elif action == "delete":
                mid = int(request.POST.get("model_id", 0))
                ModelService.delete(mid)
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)


class AibrokerPromptTemplateDetailConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/prompt_template_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tid = int(kwargs.get("template_id", 0))
        try:
            row = TemplateAdminService.get_one(tid)
        except ValueError:
            raise Http404()
        row = dict(row)
        row["constraint_type_label"] = dict_value_to_label(
            "aibroker_constraint_type", row.get("constraint_type")
        )
        row["ct_fmt"] = _format_prompt_tpl_ms(row.get("ct"))
        row["ut_fmt"] = _format_prompt_tpl_ms(row.get("ut"))
        row["input_variable_names"] = _prompt_tpl_name_list(row.get("input_variables"))
        row["output_variable_names"] = _prompt_tpl_name_list(row.get("output_variables"))
        ctx["aibroker_nav"] = "templates"
        ctx["tpl"] = row
        return ctx


class AibrokerPromptTemplateConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/prompt_templates.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            raw_rows = TemplateAdminService.list_all()
        except Exception:
            raw_rows = []
        rows = []
        for t in raw_rows:
            row = dict(t)
            row["constraint_type_label"] = dict_value_to_label(
                "aibroker_constraint_type", t.get("constraint_type")
            )
            rows.append(row)
        ctx["aibroker_nav"] = "templates"
        ctx["templates"] = rows
        ctx["templates_by_id"] = {str(t["id"]): t for t in rows}
        ctx["aibroker_constraint_options"] = get_dict_by_codes(
            "aibroker_constraint_type"
        ).get("aibroker_constraint_type", [])
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                TemplateAdminService.create_by_payload(
                    {
                        "template_key": (request.POST.get("template_key") or "").strip(),
                        "constraint_type": int(request.POST.get("constraint_type", 0)),
                        "description": (request.POST.get("description") or "").strip(),
                        "body": (request.POST.get("body") or "").strip(),
                        "input_variables": (request.POST.get("input_variables") or "").strip() or None,
                        "output_variables": (request.POST.get("output_variables") or "").strip() or None,
                        "status": int(request.POST.get("status", 1)),
                    }
                )
            elif action == "update":
                tid = int(request.POST.get("template_id", 0))
                TemplateAdminService.update_by_payload(
                    tid,
                    {
                        "description": (request.POST.get("description") or "").strip(),
                        "body": (request.POST.get("body") or "").strip(),
                        "constraint_type": int(request.POST.get("constraint_type", 0)),
                        "input_variables": (request.POST.get("input_variables") or "").strip() or None,
                        "output_variables": (request.POST.get("output_variables") or "").strip() or None,
                    },
                )
            elif action == "set_status":
                tid = int(request.POST.get("template_id", 0))
                st = int(request.POST.get("status", 0))
                TemplateAdminService.update_by_payload(tid, {"status": st})
            elif action == "delete":
                tid = int(request.POST.get("template_id", 0))
                TemplateAdminService.delete(tid)
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)
