"""Console UI for app_tcc — registration, biz/branch, transactions, manual review."""

import json
import math

from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.views.generic import TemplateView

from app_tcc.enums import BranchStatus, GlobalTxStatus
from app_tcc.services import biz_branch_service, participant_reg_service
from app_console.services import tcc_console_query
from common.enums.service_reg_status_enum import ServiceRegStatus

_PAGE = 50

_GLOBAL_TX_LABELS = {
    GlobalTxStatus.INIT: "INIT",
    GlobalTxStatus.TRYING: "TRYING",
    GlobalTxStatus.AWAIT_CONFIRM: "AWAIT_CONFIRM",
    GlobalTxStatus.CONFIRMING: "CONFIRMING",
    GlobalTxStatus.CANCELING: "CANCELING",
    GlobalTxStatus.COMMITTED: "COMMITTED",
    GlobalTxStatus.ROLLED_BACK: "ROLLED_BACK",
    GlobalTxStatus.NEEDS_MANUAL: "NEEDS_MANUAL",
}

_BRANCH_STATUS_LABELS = {
    BranchStatus.PENDING_TRY: "PENDING_TRY",
    BranchStatus.TRY_SUCCEEDED: "TRY_SUCCEEDED",
    BranchStatus.TRY_FAILED: "TRY_FAILED",
    BranchStatus.CONFIRM_SUCCEEDED: "CONFIRM_SUCCEEDED",
    BranchStatus.CONFIRM_FAILED: "CONFIRM_FAILED",
    BranchStatus.CANCEL_SUCCEEDED: "CANCEL_SUCCEEDED",
    BranchStatus.CANCEL_FAILED: "CANCEL_FAILED",
}


def _tcc_common_ctx():
    return {
        "global_tx_labels": _GLOBAL_TX_LABELS,
        "branch_status_labels": _BRANCH_STATUS_LABELS,
    }


class TccParticipantConsoleView(TemplateView):
    template_name = "console/tcc/participant_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        ctx["participants"] = participant_reg_service.list_participants()
        # Do not pass the Enum class: Django calls callables during dotted lookup.
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


class TccBizListConsoleView(TemplateView):
    template_name = "console/tcc/biz_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        ctx["participants"] = participant_reg_service.list_participants()
        pid = (self.request.GET.get("participant_id") or "").strip()
        ctx["filter_participant_id"] = int(pid) if pid.isdigit() else None
        if ctx["filter_participant_id"] is not None:
            ctx["businesses"] = biz_branch_service.list_biz_for_participant(
                ctx["filter_participant_id"]
            )
        else:
            ctx["businesses"] = biz_branch_service.list_all_biz_meta()
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        fpid = (request.POST.get("filter_participant_id") or "").strip()
        try:
            if action == "create_biz":
                biz_branch_service.create_biz_meta(
                    int(request.POST.get("participant_id", 0)),
                    name=(request.POST.get("name") or "").strip(),
                )
            elif action == "update_biz":
                biz_branch_service.update_biz_meta(
                    int(request.POST.get("biz_id", 0)),
                    name=(request.POST.get("name") or "").strip(),
                )
            elif action == "delete_biz":
                biz_branch_service.delete_biz_meta(int(request.POST.get("biz_id", 0)))
        except (ValueError, TypeError):
            pass
        red = request.path
        if fpid.isdigit():
            red += "?participant_id=" + fpid
        return HttpResponseRedirect(red)


def _branch_meta_redirect(request: HttpRequest) -> HttpResponseRedirect:
    q = (request.POST.get("participant_id") or request.GET.get("participant_id") or "").strip()
    path = request.path
    if q.isdigit():
        path += "?participant_id=" + q
    return HttpResponseRedirect(path)


class TccBranchMetaConsoleView(TemplateView):
    template_name = "console/tcc/branch_meta_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.biz_id = int(kwargs["biz_id"])
        self.biz = biz_branch_service.get_biz_meta(self.biz_id)
        if not self.biz:
            raise Http404("biz not found")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        ctx["biz"] = self.biz
        ctx["participant"] = self.biz.participant
        ctx["branches"] = biz_branch_service.list_branch_meta_for_biz(self.biz_id)
        pid_raw = (self.request.GET.get("participant_id") or "").strip()
        ctx["filter_participant_id"] = int(pid_raw) if pid_raw.isdigit() else None
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        bid = self.biz_id
        try:
            if action == "create_branch":
                brs = biz_branch_service.list_branch_meta_for_biz(bid)
                mx = max((b.branch_index for b in brs), default=-1)
                next_idx = mx + 1
                biz_branch_service.create_branch_meta(
                    bid,
                    branch_index=next_idx,
                    code=(request.POST.get("code") or "").strip(),
                    name=(request.POST.get("name") or "").strip(),
                    try_url=(request.POST.get("try_url") or "").strip(),
                    confirm_url=(request.POST.get("confirm_url") or "").strip(),
                    cancel_url=(request.POST.get("cancel_url") or "").strip(),
                )
            elif action == "update_branch":
                ukw: dict = {
                    "name": (request.POST.get("name") or "").strip(),
                    "try_url": (request.POST.get("try_url") or "").strip(),
                    "confirm_url": (request.POST.get("confirm_url") or "").strip(),
                    "cancel_url": (request.POST.get("cancel_url") or "").strip(),
                }
                code_raw = (request.POST.get("code") or "").strip()
                if code_raw:
                    ukw["code"] = code_raw
                biz_branch_service.update_branch_meta(
                    int(request.POST.get("branch_id", 0)), **ukw
                )
            elif action == "delete_branch":
                biz_branch_service.delete_branch_meta(int(request.POST.get("branch_id", 0)))
            elif action == "reorder_branches":
                raw = (request.POST.get("branch_ids_ordered") or "").strip()
                ids: list[int] = []
                for x in raw.split(","):
                    xs = x.strip()
                    if xs.isdigit():
                        ids.append(int(xs))
                biz_branch_service.reorder_branch_metas_for_biz(bid, ids)
        except (ValueError, TypeError):
            pass
        return _branch_meta_redirect(request)


class TccTxListConsoleView(TemplateView):
    template_name = "console/tcc/tx_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        raw_page = (self.request.GET.get("page") or "1").strip()
        page = int(raw_page) if raw_page.isdigit() else 1
        raw_st = (self.request.GET.get("status") or "").strip()
        status = int(raw_st) if raw_st.isdigit() else None
        total, rows = tcc_console_query.list_transactions(status=status, page=page, page_size=_PAGE)
        ctx["transactions"] = rows
        ctx["total"] = total
        ctx["page"] = page
        ctx["page_size"] = _PAGE
        ctx["total_pages"] = max(1, math.ceil(total / _PAGE) if total else 1)
        ctx["filter_status"] = status
        ctx["status_options"] = sorted(_GLOBAL_TX_LABELS.items(), key=lambda x: x[0])
        if status is not None:
            ctx["status_query_suffix"] = f"&status={status}"
        else:
            ctx["status_query_suffix"] = ""
        return ctx


class TccTxDetailConsoleView(TemplateView):
    template_name = "console/tcc/tx_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.tx_id = int(kwargs["tx_id"])
        self.tx = tcc_console_query.get_transaction(self.tx_id)
        if not self.tx:
            raise Http404("transaction not found")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        ctx["status_options"] = sorted(_GLOBAL_TX_LABELS.items(), key=lambda x: x[0])
        ctx["branch_status_options"] = sorted(_BRANCH_STATUS_LABELS.items(), key=lambda x: x[0])
        ctx["tx"] = self.tx
        ctx["branches"] = tcc_console_query.list_tx_branches(self.tx_id)
        ctx["manual_review"] = tcc_console_query.get_manual_review(self.tx_id)
        try:
            ctx["context_pretty"] = json.dumps(
                json.loads((self.tx.context or "{}").strip() or "{}"),
                ensure_ascii=False,
                indent=2,
            )
        except json.JSONDecodeError:
            ctx["context_pretty"] = self.tx.context or ""
        return ctx


class TccManualConsoleView(TemplateView):
    template_name = "console/tcc/manual_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_tcc_common_ctx())
        raw_page = (self.request.GET.get("page") or "1").strip()
        page = int(raw_page) if raw_page.isdigit() else 1
        total, rows = tcc_console_query.list_needs_manual(page=page, page_size=_PAGE)
        ctx["transactions"] = rows
        ctx["total"] = total
        ctx["page"] = page
        ctx["page_size"] = _PAGE
        ctx["total_pages"] = max(1, math.ceil(total / _PAGE) if total else 1)
        ids = [g.pk for g in rows]
        rev_map = tcc_console_query.manual_reviews_by_tx_ids(ids)
        ctx["manual_rows"] = [{"tx": g, "review": rev_map.get(g.pk)} for g in rows]
        return ctx
