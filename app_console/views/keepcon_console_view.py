"""Console UI for app_keepcon."""

from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from app_keepcon.services.device_service import KeepconDeviceService, KeepconMessageService
from app_console.services.dict_options import CODE_KEEPCON_DEVICE_TYPE, str_kv
from app_keepcon.services.reg_service import KeepconRegService
from app_console.views.reg_console_view import RegConsoleView


class KeepconRegConsoleView(RegConsoleView):
    """长连接 — 调用方（access_key 用于内部投递 API）。"""

    template_name = "console/keepcon/reg_list.html"
    reg_service = KeepconRegService


class KeepconDevicesConsoleView(TemplateView):
    template_name = "console/keepcon/devices_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = KeepconDeviceService.list_all()
        ctx["device_type_options"] = str_kv(CODE_KEEPCON_DEVICE_TYPE)
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                opts = str_kv(CODE_KEEPCON_DEVICE_TYPE)
                default_dt = opts[0][0] if opts else "1"
                KeepconDeviceService.create(
                    device_key=(request.POST.get("device_key") or "").strip(),
                    device_type=request.POST.get("device_type") or default_dt,
                    name=(request.POST.get("name") or "").strip(),
                )
            elif action == "delete":
                KeepconDeviceService.delete(int(request.POST.get("device_id", 0)))
        except ValueError:
            pass
        return HttpResponseRedirect(request.path)


class KeepconMessagesConsoleView(TemplateView):
    template_name = "console/keepcon/messages_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = KeepconDeviceService.list_all()
        raw_filter = self.request.GET.get("device_id")
        device_filter: int | None = None
        if raw_filter and raw_filter.isdigit():
            device_filter = int(raw_filter)
        ctx["device_filter"] = device_filter
        if device_filter is not None:
            ctx["messages"] = KeepconMessageService.list_for_console(
                device_row_id=device_filter,
                limit=200,
            )
        else:
            ctx["messages"] = KeepconMessageService.list_for_console(limit=200)
        return ctx
