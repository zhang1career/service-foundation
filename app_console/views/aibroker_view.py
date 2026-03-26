"""AI Broker 控制台：调用方、提供商/模型、提示模板（直接调用 app_aibroker 服务层）。"""
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView

from app_aibroker.services.provider_service import ModelService, ProviderService
from app_aibroker.services.reg_service import RegService as AibrokerRegService
from app_aibroker.services.template_admin_service import TemplateAdminService


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


class AibrokerPromptTemplateConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/prompt_templates.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            rows = TemplateAdminService.list_all()
        except Exception:
            rows = []
        ctx["aibroker_nav"] = "templates"
        ctx["templates"] = rows
        ctx["templates_by_id"] = {str(t["id"]): t for t in rows}
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                TemplateAdminService.create_by_payload(
                    {
                        "template_key": (request.POST.get("template_key") or "").strip(),
                        "version": int(request.POST.get("version", 1)),
                        "constraint_type": int(request.POST.get("constraint_type", 0)),
                        "body": (request.POST.get("body") or "").strip(),
                        "variables_schema_json": (request.POST.get("variables_schema_json") or "").strip() or None,
                        "output_schema_json": (request.POST.get("output_schema_json") or "").strip() or None,
                        "status": int(request.POST.get("status", 1)),
                    }
                )
            elif action == "update":
                tid = int(request.POST.get("template_id", 0))
                TemplateAdminService.update_by_payload(
                    tid,
                    {
                        "body": (request.POST.get("body") or "").strip(),
                        "constraint_type": int(request.POST.get("constraint_type", 0)),
                        "variables_schema_json": (request.POST.get("variables_schema_json") or "").strip() or None,
                        "output_schema_json": (request.POST.get("output_schema_json") or "").strip() or None,
                        "status": int(request.POST.get("status", 1)),
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
