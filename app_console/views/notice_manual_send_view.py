import json

from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from app_notice.enums import ChannelEnum
from app_notice.enums.broker_jiang_enum import BrokerJiangEnum
from app_notice.services.channel_broker_map import channel_to_broker_channel_ids
from app_notice.services.notice_service import enqueue_notice_by_payload
from app_notice.services.reg_service import RegService as NoticeRegService

_SESSION_FLASH_KEY = "console_notice_manual_flash"


class NoticeManualSendConsoleView(TemplateView):
    """控制台手动触发通知入队（与开放 API 同一套 enqueue 逻辑）。"""

    template_name = "console/notice/manual_send.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["channel_options"] = ChannelEnum.to_dict_list()
        ctx["jiang_mappable_channel_ids"] = list(channel_to_broker_channel_ids(BrokerJiangEnum).keys())
        ctx["jiang_mappable_channel_ids_json"] = json.dumps(ctx["jiang_mappable_channel_ids"])
        ctx["regs"] = NoticeRegService.list_all()
        ctx["default_event_id"] = int(getattr(settings, "NOTICE_CONSOLE_MANUAL_EVENT_ID", 1))
        ctx["flash"] = self.request.session.pop(_SESSION_FLASH_KEY, None)
        return ctx

    def post(self, request, *args, **kwargs):
        try:
            channel = int(request.POST.get("channel", 0))
            br = (request.POST.get("broker") or "").strip()
            broker_payload = None
            if channel in (ChannelEnum.EMAIL.value, ChannelEnum.SMS.value):
                if br:
                    raise ValueError("broker must not be set for email/sms channels")
            else:
                if not br:
                    raise ValueError("broker is required for this channel")
                broker_payload = int(br)

            payload = {
                "access_key": (request.POST.get("access_key") or "").strip(),
                "channel": channel,
                "broker": broker_payload,
                "target": (request.POST.get("target") or "").strip(),
                "subject": (request.POST.get("subject") or "").strip(),
                "content": (request.POST.get("content") or "").strip(),
                "event_id": int(request.POST.get("event_id", 0)),
            }
            result = enqueue_notice_by_payload(payload)
            request.session[_SESSION_FLASH_KEY] = {
                "ok": True,
                "notice_id": result.get("notice_id"),
                "event_id": result.get("event_id"),
            }
        except ValueError as exc:
            request.session[_SESSION_FLASH_KEY] = {"ok": False, "message": str(exc)}
        return HttpResponseRedirect(request.path)
