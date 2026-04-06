"""通知中心：通知列表与详情。"""
import app_notice.dict_registration  # noqa: F401  # register notice_* dict codes

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView

from app_notice.enums import ChannelEnum
from app_notice.repos import delete_notice_record_by_id, get_notice_record_by_id, list_notice_records_page
from app_notice.services.notice_service import enqueue_resend_notice_record
from app_notice.services.reg_service import RegService as NoticeRegService
from common.dict_catalog import dict_value_to_label
from common.utils.page_util import slice_window_for_page

from app_console.utils import format_epoch_ms_for_display

_SESSION_NOTICE_DETAIL_FLASH = "console_notice_detail_flash"


class _NoticeConsoleMixin:
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "APP_NOTICE_ENABLED", False):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)


def _notice_reg_label_map() -> dict[int, str]:
    out: dict[int, str] = {}
    try:
        for r in NoticeRegService.list_all():
            rid = int(r["id"])
            name = (r.get("name") or "").strip()
            out[rid] = name if name else f"#{rid}"
    except Exception:
        pass
    return out


def _can_resend_notice_row(channel: int, broker: int) -> bool:
    if channel in (ChannelEnum.EMAIL.value, ChannelEnum.SMS.value):
        return True
    return broker != 0


class NoticeListConsoleView(_NoticeConsoleMixin, TemplateView):
    template_name = "console/notice/notice_list.html"
    PAGE_SIZE = 30

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action == "delete":
            try:
                nid = int(request.POST.get("notice_id", 0))
                if nid > 0:
                    delete_notice_record_by_id(nid)
            except (ValueError, TypeError):
                pass
        page_q = (request.POST.get("page") or "").strip()
        if page_q.isdigit() and int(page_q) > 1:
            return HttpResponseRedirect(f"{request.path}?page={int(page_q)}")
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            page = int(self.request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        rows, total, resolved_page = list_notice_records_page(page, self.PAGE_SIZE)
        _, _, total_pages = slice_window_for_page(total, page, self.PAGE_SIZE)
        reg_map = _notice_reg_label_map()
        notices: list[dict] = []
        for r in rows:
            ch = int(r.channel)
            st = int(r.status)
            tgt = r.target or ""
            br = int(r.broker)
            broker_label = dict_value_to_label("notice_broker", br) if br != 0 else "—"
            notices.append(
                {
                    "id": r.id,
                    "reg_id": r.reg_id,
                    "reg_label": reg_map.get(int(r.reg_id), f"#{r.reg_id}"),
                    "event_id": r.event_id,
                    "channel": ch,
                    "channel_label": dict_value_to_label("notice_channel", ch),
                    "status": st,
                    "status_label": dict_value_to_label("notice_status", st),
                    "broker": br,
                    "broker_label": broker_label,
                    "target_short": (tgt[:80] + "…") if len(tgt) > 80 else tgt,
                    "ct_fmt": format_epoch_ms_for_display(r.ct),
                }
            )
        ctx["notices"] = notices
        ctx["page"] = resolved_page
        ctx["total"] = total
        ctx["total_pages"] = total_pages
        ctx["page_size"] = self.PAGE_SIZE
        ctx["has_prev"] = resolved_page > 1
        ctx["has_next"] = resolved_page < total_pages
        ctx["active"] = "notices"
        return ctx


class NoticeDetailConsoleView(_NoticeConsoleMixin, TemplateView):
    template_name = "console/notice/notice_detail.html"

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        notice_id = int(kwargs.get("notice_id", 0))
        if action == "send" and notice_id > 0:
            try:
                enqueue_resend_notice_record(notice_id)
                request.session[_SESSION_NOTICE_DETAIL_FLASH] = {"ok": True}
            except ValueError as exc:
                request.session[_SESSION_NOTICE_DETAIL_FLASH] = {"ok": False, "message": str(exc)}
            return HttpResponseRedirect(request.path)
        return HttpResponseRedirect(request.path)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        notice_id = int(kwargs.get("notice_id", 0))
        row = get_notice_record_by_id(notice_id)
        if row is None:
            raise Http404()
        reg_map = _notice_reg_label_map()
        ch = int(row.channel)
        st = int(row.status)
        br = int(row.broker)
        broker_label = dict_value_to_label("notice_broker", br) if br != 0 else "—"
        flash = self.request.session.pop(_SESSION_NOTICE_DETAIL_FLASH, None)
        ctx["row"] = {
            "id": row.id,
            "reg_id": row.reg_id,
            "reg_label": reg_map.get(int(row.reg_id), f"#{row.reg_id}"),
            "event_id": row.event_id,
            "channel": ch,
            "channel_label": dict_value_to_label("notice_channel", ch),
            "status": st,
            "status_label": dict_value_to_label("notice_status", st),
            "target": row.target or "",
            "subject": row.subject or "",
            "content": row.content or "",
            "provider": row.provider or "",
            "message": row.message or "",
            "broker": br,
            "broker_label": broker_label,
            "ct_fmt": format_epoch_ms_for_display(row.ct),
            "ut_fmt": format_epoch_ms_for_display(row.ut),
        }
        ctx["show_send"] = st == 0
        ctx["can_resend"] = _can_resend_notice_row(ch, br)
        ctx["list_url"] = reverse("console:notice-notices")
        ctx["active"] = "notices"
        ctx["flash"] = flash
        return ctx
