"""AI Broker 控制台：调用方、提供商/模型、提示词模版（直接调用 app_aibroker 服务层）。"""
import json
import logging

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.repos.call_log_repo import (
    delete_call_log_by_id,
    delete_call_logs_by_ids,
    get_call_log_by_id,
    list_call_logs_page,
)
from app_aibroker.repos.model_repo import get_model_by_id
from app_aibroker.repos.provider_repo import get_provider_by_id
from app_aibroker.repos.reg_repo import get_reg_by_id as aibroker_get_reg_by_id
from app_aibroker.services.provider_service import ModelService, ProviderService
from app_aibroker.services.reg_service import RegService as AibrokerRegService
from app_aibroker.services.template_admin_service import TemplateAdminService
from app_aibroker.services.aibroker_multipart_service import (
    parse_meta_json,
    upload_one_aibroker_file,
)
from app_aibroker.services.template_render_service import parse_param_specs
from app_aibroker.services.text_generation_service import (
    _ai_model_param_specs_detail_rows,
    generate_text,
)
from app_aibroker.services.llm_client_service import fetch_json
from common.consts.response_const import (
    RET_AI_ERROR,
    RET_INVALID_PARAM,
    RET_JSON_PARSE_ERROR,
    RET_OK,
    RET_UNKNOWN,
)
from app_console.utils import embed_dict_as_json_script_body, format_epoch_ms_for_display
from common.dict_catalog import dict_value_to_label, get_dict_by_codes
from common.exceptions.base_exception import generic_message_for_ret
from common.pojo.response import Response as ApiResponse
from common.utils.http_util import attach_request_id_header, resolve_request_id, response_as_dict
from common.utils.json_util import API_JSON_DUMPS_PARAMS
from common.utils.page_util import slice_window_for_page

logger = logging.getLogger(__name__)


def _prompt_tpl_name_list(s) -> list[str]:
    """解析 param_specs / resp_specs JSON 为有序名称列表（与控制台列表编辑器一致）。"""
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


def _prompt_tpl_spec_rows(s) -> list[dict]:
    """param_specs 解析为 {name, kind} 列表（详情页展示）。"""
    specs = parse_param_specs(s)
    return [{"name": x["name"], "kind": x.get("kind", "text")} for x in specs]


def _aibroker_call_log_label_maps() -> tuple[dict[int, str], dict[int, str], dict[int, str], dict[int, str]]:
    """从 aibroker 库加载调用方 / 模板 / 提供商 / 模型，供调用日志列表与详情解析展示名。"""
    reg_map: dict[int, str] = {}
    tpl_map: dict[int, str] = {}
    prov_map: dict[int, str] = {}
    model_map: dict[int, str] = {}
    try:
        for r in AibrokerRegService.list_all():
            rid = int(r["id"])
            name = (r.get("name") or "").strip()
            reg_map[rid] = name if name else f"#{rid}"
    except Exception:
        pass
    try:
        for t in TemplateAdminService.list_all():
            tid = int(t["id"])
            key = (t.get("template_key") or "").strip()
            tpl_map[tid] = key if key else f"模板 #{tid}"
    except Exception:
        pass
    try:
        providers = ProviderService.list_all()
        for p in providers:
            pid = int(p["id"])
            name = (p.get("name") or "").strip()
            prov_map[pid] = name if name else f"#{pid}"
        for p in providers:
            pid = int(p["id"])
            for m in ModelService.list_for_provider(pid):
                mid = int(m["id"])
                mn = (m.get("model_name") or "").strip()
                model_map[mid] = mn if mn else f"#{mid}"
    except Exception:
        pass
    return reg_map, tpl_map, prov_map, model_map


def _call_log_dim_label(dim_map: dict[int, str], pk: int) -> str:
    if pk <= 0:
        return "—"
    label = dim_map.get(int(pk))
    if label:
        return label
    return f"未知 (#{pk})"


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
            ctx["regs"] = AibrokerRegService.list_all_for_console()
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
                        "url_path": (request.POST.get("url_path") or "").strip(),
                        "api_key": (request.POST.get("api_key") or "").strip(),
                        "status": int(request.POST.get("status", 1)),
                    }
                )
            elif action == "update":
                pid = int(request.POST.get("provider_id", 0))
                payload = {
                    "name": (request.POST.get("name") or "").strip(),
                    "base_url": (request.POST.get("base_url") or "").strip(),
                    "url_path": (request.POST.get("url_path") or "").strip(),
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


class AibrokerProviderDetailConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/provider_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "providers"
        pid = int(kwargs.get("provider_id", 0))
        try:
            ctx["provider"] = ProviderService.get_one(pid)
        except ValueError:
            raise Http404()
        ctx["provider_id"] = pid
        ctx["ct_fmt"] = format_epoch_ms_for_display(ctx["provider"].get("ct"))
        ctx["ut_fmt"] = format_epoch_ms_for_display(ctx["provider"].get("ut"))
        return ctx


class AibrokerModelConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/models.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "models"
        pid = int(kwargs.get("provider_id", 0))
        ctx["provider_id"] = pid
        ctx["provider"] = None
        ctx["models"] = []
        ctx["aibroker_model_capability_options"] = []
        try:
            p = ProviderService.get_one(pid)
            ctx["provider"] = p
            raw_models = ModelService.list_for_provider(pid)
            rows = []
            for m in raw_models:
                row = dict(m)
                row["capability_label"] = dict_value_to_label(
                    "aibroker_model_capability", row.get("capability")
                )
                rows.append(row)
            ctx["models"] = rows
            ctx["model_param_specs_by_id"] = {
                str(r["id"]): (r.get("param_specs") or "") for r in rows
            }
            ctx["aibroker_model_capability_options"] = get_dict_by_codes(
                "aibroker_model_capability"
            ).get("aibroker_model_capability", [])
        except ValueError:
            ctx["model_param_specs_by_id"] = {}
            pass
        except Exception:
            logger.exception(
                "[aibroker] console model list failed (provider_id=%s)",
                pid,
            )
            ctx["model_param_specs_by_id"] = {}
            pass
        if "model_param_specs_by_id" not in ctx:
            ctx["model_param_specs_by_id"] = {}
        ctx["model_param_specs_embed"] = embed_dict_as_json_script_body(
            ctx["model_param_specs_by_id"]
        )
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
                        "param_specs": (request.POST.get("param_specs") or "").strip(),
                    }
                )
            elif action == "update":
                mid = int(request.POST.get("model_id", 0))
                ModelService.update(
                    mid,
                    {
                        "model_name": (request.POST.get("model_name") or "").strip(),
                        "capability": int(request.POST.get("capability", 0)),
                        "param_specs": (request.POST.get("param_specs") or "").strip(),
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
        except Exception:
            logger.exception(
                "[aibroker] console model POST failed action=%s provider_id=%s",
                action,
                provider_id,
            )
            raise
        return HttpResponseRedirect(request.path)


class AibrokerModelDetailConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/model_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pid = int(kwargs.get("provider_id", 0))
        mid = int(kwargs.get("model_id", 0))
        try:
            prov = ProviderService.get_one(pid)
        except ValueError:
            raise Http404()
        m = get_model_by_id(mid)
        if m is None or int(m.provider_id) != pid:
            raise Http404()
        row = ModelService._to_dict(m)
        row["capability_label"] = dict_value_to_label(
            "aibroker_model_capability", row.get("capability")
        )
        row["ct_fmt"] = format_epoch_ms_for_display(row.get("ct"))
        row["ut_fmt"] = format_epoch_ms_for_display(row.get("ut"))
        row["param_specs_detail_rows"] = _ai_model_param_specs_detail_rows(row.get("param_specs"))
        ctx["aibroker_nav"] = "models"
        ctx["provider_id"] = pid
        ctx["provider"] = prov
        ctx["model"] = row
        return ctx


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
        row["ct_fmt"] = format_epoch_ms_for_display(row.get("ct"))
        row["ut_fmt"] = format_epoch_ms_for_display(row.get("ut"))
        row["param_specs_rows"] = _prompt_tpl_spec_rows(row.get("param_specs"))
        row["resp_specs_names"] = _prompt_tpl_name_list(row.get("resp_specs"))
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
                        "param_specs": (request.POST.get("param_specs") or "").strip() or None,
                        "resp_specs": (request.POST.get("resp_specs") or "").strip() or None,
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
                        "param_specs": (request.POST.get("param_specs") or "").strip() or None,
                        "resp_specs": (request.POST.get("resp_specs") or "").strip() or None,
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


class AibrokerCallLogConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/call_logs.html"
    PAGE_SIZE = 30

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "call_logs"
        try:
            page = int(self.request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            rows, total, resolved_page = list_call_logs_page(page, self.PAGE_SIZE)
        except Exception:
            rows, total, resolved_page = [], 0, 1
        _, _, total_pages = slice_window_for_page(total, page, self.PAGE_SIZE)
        reg_m, tpl_m, prov_m, model_m = _aibroker_call_log_label_maps()
        logs: list[dict] = []
        for r in rows:
            logs.append(
                {
                    "id": r.id,
                    "reg_id": r.reg_id,
                    "template_id": r.template_id,
                    "provider_id": r.provider_id,
                    "model_id": r.model_id,
                    "reg_label": _call_log_dim_label(reg_m, r.reg_id),
                    "template_label": _call_log_dim_label(tpl_m, r.template_id),
                    "provider_label": _call_log_dim_label(prov_m, r.provider_id),
                    "model_label": _call_log_dim_label(model_m, r.model_id),
                    "latency_ms": r.latency_ms,
                    "success": r.success,
                    "success_label": "成功" if int(r.success) == 1 else "失败",
                    "error_message": r.error_message or "",
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
                log_id = int(request.POST.get("log_id", 0))
                if log_id > 0:
                    delete_call_log_by_id(log_id)
            except (ValueError, TypeError):
                pass
        elif action == "bulk_delete":
            raw_ids = request.POST.getlist("log_ids")
            parsed: list[int] = []
            for x in raw_ids:
                try:
                    v = int(x)
                    if v > 0:
                        parsed.append(v)
                except (TypeError, ValueError):
                    pass
            if parsed:
                delete_call_logs_by_ids(parsed)
        page_q = (request.POST.get("page") or "").strip()
        if page_q.isdigit() and int(page_q) > 1:
            return HttpResponseRedirect(f"{request.path}?page={int(page_q)}")
        return HttpResponseRedirect(request.path)


class AibrokerCallLogDetailConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/call_log_detail.html"

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        log_id = int(kwargs.get("log_id", 0))
        if action == "delete" and log_id > 0:
            try:
                delete_call_log_by_id(log_id)
            except Exception:
                pass
            return HttpResponseRedirect(reverse("console:aibroker-call-logs"))
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        log_id = int(kwargs.get("log_id", 0))
        row = get_call_log_by_id(log_id)
        if row is None:
            raise Http404()
        reg_m, tpl_m, prov_m, model_m = _aibroker_call_log_label_maps()
        ctx["aibroker_nav"] = "call_logs"
        ctx["log"] = {
            "id": row.id,
            "reg_id": row.reg_id,
            "template_id": row.template_id,
            "provider_id": row.provider_id,
            "model_id": row.model_id,
            "reg_label": _call_log_dim_label(reg_m, row.reg_id),
            "template_label": _call_log_dim_label(tpl_m, row.template_id),
            "provider_label": _call_log_dim_label(prov_m, row.provider_id),
            "model_label": _call_log_dim_label(model_m, row.model_id),
            "latency_ms": row.latency_ms,
            "success": row.success,
            "success_label": "成功" if int(row.success) == 1 else "失败",
            "error_message": row.error_message or "",
            "ct_fmt": format_epoch_ms_for_display(row.ct),
        }
        return ctx


def _aibroker_reg_for_console_debug():
    """Reg for console debug call logs; primary key from env AIBROKER_REG_ID_TEST."""
    rid = int(getattr(settings, "AIBROKER_REG_ID_TEST", 0))
    if rid <= 0:
        return None
    return aibroker_get_reg_by_id(rid)


def _aibroker_debug_json_response(
    request,
    *,
    error_code: int,
    message: str = "",
    data=None,
    detail: str = "",
):
    """
    Console debug invoke must not return DRF Response from a plain Django View:
    DRF Response requires accepted_renderer (set by APIView); otherwise rendering raises
    AssertionError and UnifiedExceptionMiddleware returns RET_UNKNOWN without a clear cause.
    """
    rid = resolve_request_id(request)
    obj = ApiResponse(errorCode=error_code, data=data, message=message, detail=detail, _req_id=rid)
    payload = response_as_dict(obj)
    resp = JsonResponse(payload, status=200, json_dumps_params=API_JSON_DUMPS_PARAMS)
    attach_request_id_header(resp, rid)
    return resp


def _normalize_path_with_task_id(path_template: str, task_id: str) -> str:
    path = (path_template or "").strip()
    if not path:
        raise ValueError("ai_provider.url_path is empty")
    if ":task_id" not in path:
        raise ValueError("ai_provider.url_path must contain :task_id placeholder")
    return path.replace(":task_id", task_id)


class AibrokerDebugConsoleView(_AibrokerConsoleMixin, TemplateView):
    template_name = "console/aibroker/debug.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["aibroker_nav"] = "debug"
        try:
            raw_templates = TemplateAdminService.list_all()
        except Exception:
            raw_templates = []
        active_templates = [t for t in raw_templates if int(t.get("status", 0)) == 1]
        try:
            raw_providers = ProviderService.list_all()
        except Exception:
            raw_providers = []
        active_providers = [p for p in raw_providers if int(p.get("status", 0)) == 1]
        models_by_provider: dict[str, list[dict]] = {}
        for p in active_providers:
            pid = int(p["id"])
            try:
                models = ModelService.list_for_provider(pid)
            except Exception:
                models = []
            active_models = [m for m in models if int(m.get("status", 0)) == 1]
            if active_models:
                models_by_provider[str(pid)] = [
                    {
                        "id": int(m["id"]),
                        "model_name": m.get("model_name") or "",
                        "param_specs": m.get("param_specs") or "",
                        "capability": int(m.get("capability", ModelCapabilityEnum.CHAT)),
                    }
                    for m in active_models
                ]
        ctx["debug_templates"] = active_templates
        ctx["debug_providers"] = active_providers
        ctx["debug_boot"] = {
            "templatesById": {
                str(t["id"]): {"param_specs": t.get("param_specs") or ""}
                for t in active_templates
            },
            "modelsByProvider": models_by_provider,
        }
        ctx["has_debug_reg"] = _aibroker_reg_for_console_debug() is not None
        return ctx


class AibrokerDebugInvokeView(_AibrokerConsoleMixin, View):
    def post(self, request, *args, **kwargs):
        reg = _aibroker_reg_for_console_debug()
        if reg is None:
            cfg_rid = int(getattr(settings, "AIBROKER_REG_ID_TEST", 0))
            if cfg_rid <= 0:
                dbg_msg = (
                    "请在 .env 中设置 AIBROKER_REG_ID_TEST 为正整数"
                    "（控制台调试写入 call_log 的 reg_id）"
                )
            else:
                dbg_msg = (
                    f"环境变量 AIBROKER_REG_ID_TEST={cfg_rid} 在数据库中无对应调用方，请核对"
                )
            return _aibroker_debug_json_response(
                request,
                error_code=RET_AI_ERROR,
                message=dbg_msg,
            )

        content_type = (request.content_type or "").lower()
        meta_obj: dict | None = None

        if "multipart/form-data" in content_type:
            meta_obj, meta_err = parse_meta_json(request.POST.get("meta"))
            if meta_err:
                return _aibroker_debug_json_response(
                    request,
                    error_code=RET_INVALID_PARAM,
                    message=meta_err,
                )
            if request.FILES:
                return _aibroker_debug_json_response(
                    request,
                    error_code=RET_INVALID_PARAM,
                    message="files are not accepted in this endpoint; upload first and pass image URL",
                )
        else:
            try:
                meta_obj = json.loads(request.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return _aibroker_debug_json_response(
                    request,
                    error_code=RET_JSON_PARSE_ERROR,
                    message="invalid JSON",
                )

        if not isinstance(meta_obj, dict):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="body must be a JSON object",
            )

        variables = meta_obj.get("variables")
        if variables is not None and not isinstance(variables, dict):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="variables must be an object",
            )
        model_params = meta_obj.get("model_params")
        if model_params is not None and not isinstance(model_params, dict):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="model_params must be an object",
            )

        try:
            template_id = int(meta_obj.get("template_id"))
            model_id = int(meta_obj.get("model_id"))
        except (TypeError, ValueError):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="template_id and model_id must be integers",
            )

        inner: dict = {
            "template_id": template_id,
            "model_id": model_id,
            "variables": variables or {},
            "model_params": model_params or {},
        }
        inner.pop("attachments", None)

        try:
            result, gen_err = generate_text(reg, inner, idempotency_key=None)
        except Exception as exc:
            logger.exception(
                "[aibroker] console debug invoke failed",
                extra={"request_id": resolve_request_id(request)},
            )
            return _aibroker_debug_json_response(
                request,
                error_code=RET_UNKNOWN,
                message=generic_message_for_ret(RET_UNKNOWN),
                detail=repr(exc) if settings.DEBUG else "",
            )
        if gen_err:
            logger.warning(
                "[aibroker] console debug invoke generate_text failed: %s",
                gen_err,
                extra={"request_id": resolve_request_id(request)},
            )
            return _aibroker_debug_json_response(
                request,
                error_code=RET_AI_ERROR,
                message=gen_err,
            )
        return _aibroker_debug_json_response(request, error_code=RET_OK, data=result)


class AibrokerDebugVideoResultView(_AibrokerConsoleMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            meta_obj = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_JSON_PARSE_ERROR,
                message="invalid JSON",
            )
        if not isinstance(meta_obj, dict):
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="body must be a JSON object",
            )
        task_id = (meta_obj.get("task_id") or "").strip()
        if not task_id:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="task_id is required",
            )
        provider_id = int(getattr(settings, "AI_PROVIDER_ID_GET_VIDEO", 0))
        if provider_id <= 0:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_AI_ERROR,
                message="请在 .env 中设置 AI_PROVIDER_ID_GET_VIDEO 为正整数",
            )
        provider = get_provider_by_id(provider_id)
        if provider is None or int(provider.status) != 1:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_AI_ERROR,
                message=f"AI_PROVIDER_ID_GET_VIDEO={provider_id} 对应 provider 不存在或已禁用",
            )
        try:
            full_path = _normalize_path_with_task_id(provider.url_path, task_id)
            upstream = fetch_json(provider, method="GET", path=full_path)
        except ValueError as exc:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message=str(exc),
            )
        except Exception as exc:
            logger.exception(
                "[aibroker] console debug video result failed",
                extra={"request_id": resolve_request_id(request)},
            )
            return _aibroker_debug_json_response(
                request,
                error_code=RET_AI_ERROR,
                message="查询视频任务结果失败",
                detail=repr(exc) if settings.DEBUG else "",
            )
        result_url = ""
        if isinstance(upstream, dict):
            data_obj = upstream.get("data")
            if isinstance(data_obj, dict):
                x = data_obj.get("result_url")
                if isinstance(x, str):
                    result_url = x.strip()
        return _aibroker_debug_json_response(
            request,
            error_code=RET_OK,
            data={
                "task_id": task_id,
                "provider_id": provider_id,
                "full_path": full_path,
                "result_url": result_url,
                "upstream": upstream,
            },
        )


class AibrokerDebugUploadImageView(_AibrokerConsoleMixin, View):
    def post(self, request, *args, **kwargs):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message="missing file",
            )
        item, err = upload_one_aibroker_file(uploaded)
        if err:
            return _aibroker_debug_json_response(
                request,
                error_code=RET_INVALID_PARAM,
                message=err,
            )
        return _aibroker_debug_json_response(request, error_code=RET_OK, data=item)
