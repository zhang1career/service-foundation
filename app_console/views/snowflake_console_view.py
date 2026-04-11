import json

from django.views.generic import TemplateView

from app_console.views.reg_console_view import RegConsoleView
from app_snowflake.services.reg_service import RegService


class SnowflakeCallerListView(RegConsoleView):
    template_name = "console/snowflake/callers_list.html"
    reg_service = RegService


class SnowflakeGenerateView(TemplateView):
    template_name = "console/snowflake/generate.html"


class SnowflakeParseView(TemplateView):
    template_name = "console/snowflake/parse.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from app_snowflake.config import get_app_config
        from app_snowflake.consts import snowflake_const as sc

        cfg = get_app_config()
        ctx["snowflake_parse_config_json"] = json.dumps(
            {
                "start_timestamp": cfg["start_timestamp"],
                "timestamp_shift": sc.TIMESTAMP_SHIFT,
                "datacenter_shift": sc.DATACENTER_SHIFT,
                "machine_shift": sc.MACHINE_SHIFT,
                "recount_shift": sc.RECOUNT_SHIFT,
                "business_shift": sc.BUSINESS_SHIFT,
                "datacenter_bits": sc.DATACENTER_BITS,
                "machine_bits": sc.MACHINE_BITS,
                "recount_bits": sc.RECOUNT_BITS,
                "business_bits": sc.BUSINESS_BITS,
                "mask_sequence": sc.MASK_SEQUENCE,
            }
        )
        return ctx


class SnowflakeHistoryView(TemplateView):
    template_name = "console/snowflake/history.html"
