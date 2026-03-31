from unittest import TestCase
from unittest.mock import MagicMock

from app_aibroker.services.template_render_service import (
    parse_param_specs,
    render_template_body_with_specs,
)


class TemplateRenderSpecsTest(TestCase):
    def test_parse_skips_non_string_raw(self):
        self.assertEqual(parse_param_specs(MagicMock()), [])

    def test_render_omits_media_vars_from_format(self):
        tpl = MagicMock()
        tpl.body = "T {a}"
        specs = parse_param_specs(
            '[{"name":"a","kind":"text"},{"name":"img","kind":"image"}]'
        )
        out = render_template_body_with_specs(tpl, {"a": "hello"}, specs)
        self.assertEqual(out, "T hello")
