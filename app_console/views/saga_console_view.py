"""Console UI for app_saga — participants, flows/steps, instances."""

import json
import math

from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.views.generic import TemplateView

from app_saga.enums import (
    SagaInstanceStatus,
    SagaStepActionStatus,
    SagaStepCompensateStatus,
)
from app_saga.services import flow_admin_service, participant_reg_service
from app_console.services import saga_console_query
from common.enums.service_reg_status_enum import ServiceRegStatus

_PAGE = 50

_INSTANCE_STATUS_LABELS = {
    SagaInstanceStatus.PENDING: "PENDING",
    SagaInstanceStatus.RUNNING: "RUNNING",
    SagaInstanceStatus.COMPENSATING: "COMPENSATING",
    SagaInstanceStatus.COMPLETED: "COMPLETED",
    SagaInstanceStatus.ROLLED_BACK: "ROLLED_BACK",
    SagaInstanceStatus.FAILED: "FAILED",
}

_ACTION_STATUS_LABELS = {
    SagaStepActionStatus.PENDING: "PENDING",
    SagaStepActionStatus.SUCCEEDED: "SUCCEEDED",
    SagaStepActionStatus.FAILED: "FAILED",
}

_COMPENSATE_STATUS_LABELS = {
    SagaStepCompensateStatus.PENDING: "PENDING",
    SagaStepCompensateStatus.SUCCEEDED: "SUCCEEDED",
    SagaStepCompensateStatus.FAILED: "FAILED",
    SagaStepCompensateStatus.SKIPPED: "SKIPPED",
}


def _saga_common_ctx():
    return {
        "instance_status_labels": _INSTANCE_STATUS_LABELS,
        "action_status_labels": _ACTION_STATUS_LABELS,
        "compensate_status_labels": _COMPENSATE_STATUS_LABELS,
    }


class SagaParticipantConsoleView(TemplateView):
    template_name = "console/saga/participant_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_saga_common_ctx())
        ctx["participants"] = participant_reg_service.list_participants()
        ctx["reg_status_enabled"] = ServiceRegStatus.ENABLED.value
        ctx["reg_status_disabled"] = ServiceRegStatus.DISABLED.value
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                participant_reg_service.create_participant(
                    name=(request.POST.get("name") or "").strip(),
                    status=ServiceRegStatus.ENABLED.value,
                )
            elif action == "update":
                pk = int(request.POST.get("participant_id", 0))
                participant_reg_service.update_participant(
                    pk,
                    name=(request.POST.get("name") or "").strip(),
                )
            elif action == "set_status":
                pk = int(request.POST.get("participant_id", 0))
                st = int(request.POST.get("status", 0))
                if st not in ServiceRegStatus.values():
                    st = ServiceRegStatus.DISABLED.value
                participant_reg_service.update_participant(pk, status=st)
            elif action == "delete":
                pk = int(request.POST.get("participant_id", 0))
                participant_reg_service.delete_participant(pk)
        except (ValueError, TypeError):
            pass
        return HttpResponseRedirect(request.path)


class SagaFlowListConsoleView(TemplateView):
    template_name = "console/saga/flow_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_saga_common_ctx())
        ctx["participants"] = participant_reg_service.list_participants()
        pid = (self.request.GET.get("participant_id") or "").strip()
        ctx["filter_participant_id"] = int(pid) if pid.isdigit() else None
        if ctx["filter_participant_id"] is not None:
            ctx["flows"] = flow_admin_service.list_flows_for_participant(
                ctx["filter_participant_id"]
            )
        else:
            ctx["flows"] = flow_admin_service.list_all_flows()
        ctx["reg_status_enabled"] = ServiceRegStatus.ENABLED.value
        ctx["reg_status_disabled"] = ServiceRegStatus.DISABLED.value
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        fpid = (request.POST.get("filter_participant_id") or "").strip()
        try:
            if action == "create_flow":
                flow_admin_service.create_flow(
                    participant_id=int(request.POST.get("participant_id", 0)),
                    name=(request.POST.get("name") or "").strip(),
                    status=ServiceRegStatus.ENABLED.value,
                )
            elif action == "update_flow":
                flow_admin_service.update_flow(
                    int(request.POST.get("flow_id", 0)),
                    name=(request.POST.get("name") or "").strip(),
                )
            elif action == "set_flow_status":
                st = int(request.POST.get("status", 0))
                if st not in ServiceRegStatus.values():
                    st = ServiceRegStatus.DISABLED.value
                flow_admin_service.update_flow(
                    int(request.POST.get("flow_id", 0)),
                    status=st,
                )
            elif action == "delete_flow":
                flow_admin_service.delete_flow(int(request.POST.get("flow_id", 0)))
        except (ValueError, TypeError):
            pass
        red = request.path
        if fpid.isdigit():
            red += "?participant_id=" + fpid
        return HttpResponseRedirect(red)


def _flow_steps_redirect(request: HttpRequest) -> HttpResponseRedirect:
    q = (request.POST.get("participant_id") or request.GET.get("participant_id") or "").strip()
    path = request.path
    if q.isdigit():
        path += "?participant_id=" + q
    return HttpResponseRedirect(path)


class SagaFlowStepsConsoleView(TemplateView):
    template_name = "console/saga/flow_step_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.flow_id = int(kwargs["flow_id"])
        self.flow = saga_console_query.get_flow_for_console(self.flow_id)
        if not self.flow:
            raise Http404("flow not found")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_saga_common_ctx())
        ctx["flow"] = self.flow
        ctx["participant"] = self.flow.participant
        ctx["steps"] = flow_admin_service.list_steps_for_flow(self.flow_id)
        pid_raw = (self.request.GET.get("participant_id") or "").strip()
        ctx["filter_participant_id"] = int(pid_raw) if pid_raw.isdigit() else None
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        fid = self.flow_id
        try:
            if action == "create_step":
                ncf = int((request.POST.get("is_need_confirm") or 0) or 0)
                if ncf not in (0, 1):
                    ncf = 0
                flow_admin_service.create_flow_step(
                    flow_id=fid,
                    step_code=(request.POST.get("step_code") or "").strip(),
                    name=(request.POST.get("name") or "").strip(),
                    action_url=(request.POST.get("action_url") or "").strip(),
                    compensate_url=(request.POST.get("compensate_url") or "").strip(),
                    timeout_sec=int(request.POST.get("timeout_sec") or 30),
                    max_retries=int(request.POST.get("max_retries") or 10),
                    is_need_confirm=ncf,
                )
            elif action == "update_step":
                ncf = int((request.POST.get("is_need_confirm") or 0) or 0)
                if ncf not in (0, 1):
                    ncf = 0
                flow_admin_service.update_flow_step(
                    int(request.POST.get("step_id", 0)),
                    step_code=(request.POST.get("step_code") or "").strip(),
                    name=(request.POST.get("name") or "").strip(),
                    action_url=(request.POST.get("action_url") or "").strip(),
                    compensate_url=(request.POST.get("compensate_url") or "").strip(),
                    timeout_sec=int(request.POST.get("timeout_sec") or 30),
                    max_retries=int(request.POST.get("max_retries") or 10),
                    is_need_confirm=ncf,
                )
            elif action == "update_step_need_confirm":
                ncf = int((request.POST.get("is_need_confirm") or 0) or 0)
                if ncf not in (0, 1):
                    ncf = 0
                flow_admin_service.update_flow_step(
                    int(request.POST.get("step_id", 0)),
                    is_need_confirm=ncf,
                )
            elif action == "delete_step":
                flow_admin_service.delete_flow_step(int(request.POST.get("step_id", 0)))
            elif action == "reorder_steps":
                raw = (request.POST.get("step_ids_ordered") or "").strip()
                ids: list[int] = []
                for x in raw.split(","):
                    xs = x.strip()
                    if xs.isdigit():
                        ids.append(int(xs))
                flow_admin_service.reorder_flow_steps(fid, ids)
        except (ValueError, TypeError):
            pass
        return _flow_steps_redirect(request)


class SagaInstanceListConsoleView(TemplateView):
    template_name = "console/saga/instance_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_saga_common_ctx())
        raw_page = (self.request.GET.get("page") or "1").strip()
        page = int(raw_page) if raw_page.isdigit() else 1
        raw_st = (self.request.GET.get("status") or "").strip()
        status = int(raw_st) if raw_st.isdigit() else None
        total, rows = saga_console_query.list_instances(
            status=status, page=page, page_size=_PAGE
        )
        ctx["instances"] = rows
        ctx["total"] = total
        ctx["page"] = page
        ctx["page_size"] = _PAGE
        ctx["total_pages"] = max(1, math.ceil(total / _PAGE) if total else 1)
        ctx["filter_status"] = status
        ctx["status_options"] = saga_console_query.list_status_options()
        if status is not None:
            ctx["status_query_suffix"] = f"&status={status}"
        else:
            ctx["status_query_suffix"] = ""
        return ctx


class SagaInstanceDetailConsoleView(TemplateView):
    template_name = "console/saga/instance_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.instance_id = int(kwargs["instance_id"])
        self.inst = saga_console_query.get_instance(self.instance_id)
        if not self.inst:
            raise Http404("instance not found")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_saga_common_ctx())
        ctx["inst"] = self.inst
        ctx["step_runs"] = saga_console_query.list_step_runs(self.instance_id)
        ctx["status_options"] = saga_console_query.list_status_options()
        ctx["action_status_options"] = sorted(
            [(k.value, v) for k, v in _ACTION_STATUS_LABELS.items()],
            key=lambda x: x[0],
        )
        ctx["compensate_status_options"] = sorted(
            [(k.value, v) for k, v in _COMPENSATE_STATUS_LABELS.items()],
            key=lambda x: x[0],
        )
        try:
            ctx["context_pretty"] = json.dumps(
                json.loads((self.inst.context or "{}").strip() or "{}"),
                ensure_ascii=False,
                indent=2,
            )
        except json.JSONDecodeError:
            ctx["context_pretty"] = self.inst.context or ""
        return ctx
