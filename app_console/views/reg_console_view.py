from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from app_notice.services.reg_service import RegService as NoticeRegService
from app_verify.services.reg_service import RegService as VerifyRegService


class RegConsoleView(TemplateView):
    """管理 notice 或 verify 注册方（直接调用对应 RegService）。"""

    reg_service = None

    def _list_regs(self):
        try:
            return self.reg_service.list_all()
        except Exception:
            return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["regs"] = self._list_regs()
        return ctx

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        try:
            if action == "create":
                self.reg_service.create_by_payload(
                    {
                        "name": (request.POST.get("name") or "").strip(),
                        "status": 1,
                    }
                )
            elif action == "update":
                rid = int(request.POST.get("reg_id", 0))
                self.reg_service.update_by_payload(
                    rid,
                    {
                        "name": (request.POST.get("name") or "").strip(),
                    },
                )
            elif action == "set_status":
                rid = int(request.POST.get("reg_id", 0))
                st = int(request.POST.get("status", 0))
                self.reg_service.update_by_payload(rid, {"status": st})
            elif action == "delete":
                rid = int(request.POST.get("reg_id", 0))
                self.reg_service.delete(rid)
        except (ValueError, KeyError):
            pass
        return HttpResponseRedirect(request.path)


class NoticeRegConsoleView(RegConsoleView):
    template_name = "console/notice/reg_list.html"
    reg_service = NoticeRegService


class VerifyRegConsoleView(RegConsoleView):
    template_name = "console/verify/caller_list.html"
    reg_service = VerifyRegService
