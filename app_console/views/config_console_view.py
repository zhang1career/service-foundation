"""Configuration center console (app_config)."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from app_config.services.condition_field_service import ConfigConditionFieldService
from app_config.services.config_entry_service import ConfigEntryService
from app_config.services.reg_service import ConfigRegService
from app_console.views.reg_console_view import RegConsoleView


class ConfigRegConsoleView(RegConsoleView):
    """配置中心 — 调用方（reg）。"""

    template_name = "console/config/reg_list.html"
    reg_service = ConfigRegService


class ConfigEntriesConsoleView(TemplateView):
    template_name = "console/config/entries_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["entries"] = ConfigEntryService.list_all()
        ctx["regs"] = ConfigRegService.list_all()
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                ConfigEntryService.create(
                    rid=int(request.POST.get("rid", 0)),
                    config_key=(request.POST.get("config_key") or "").strip(),
                    condition=(request.POST.get("condition") or "").strip() or "{}",
                    value=(request.POST.get("value") or "").strip(),
                )
            elif action == "update":
                ConfigEntryService.update(
                    int(request.POST.get("entry_id", 0)),
                    config_key=(request.POST.get("config_key") or "").strip() or None,
                    condition=(request.POST.get("condition") or "").strip() or None,
                    value=(request.POST.get("value") or "").strip() or None,
                )
            elif action == "delete":
                ConfigEntryService.delete(int(request.POST.get("entry_id", 0)))
        except ValueError as exc:
            messages.error(request, str(exc))
        except (KeyError, TypeError):
            pass
        return HttpResponseRedirect(request.path)


class ConfigConditionFieldsConsoleView(TemplateView):
    template_name = "console/config/condition_fields_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["fields"] = ConfigConditionFieldService.list_all()
        ctx["regs"] = ConfigRegService.list_all()
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                ConfigConditionFieldService.create(
                    rid=int(request.POST.get("rid", 0)),
                    field_key=(request.POST.get("field_key") or "").strip(),
                    description=(request.POST.get("description") or "").strip(),
                )
            elif action == "update":
                ConfigConditionFieldService.update(
                    int(request.POST.get("field_id", 0)),
                    field_key=(request.POST.get("field_key") or "").strip() or None,
                    description=(request.POST.get("description") or "").strip() or None,
                )
            elif action == "delete":
                ConfigConditionFieldService.delete(int(request.POST.get("field_id", 0)))
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)
