from unittest import TestCase
from unittest.mock import MagicMock

from app_aibroker.services.template_render_service import validate_output


class TemplateRenderServiceTest(TestCase):
    def test_validate_output_accepts_markdown_json_block(self):
        tpl = MagicMock(constraint_type=1, resp_specs='[{"name":"answer"}]')
        model_text = """```json
{"answer":"ok"}
```"""

        out = validate_output(tpl, model_text)

        self.assertEqual(out, '{"answer": "ok"}')

    def test_validate_output_rejects_missing_required_key(self):
        tpl = MagicMock(constraint_type=1, resp_specs='[{"name":"answer"}]')

        with self.assertRaises(ValueError) as ctx:
            validate_output(tpl, '{"other":"x"}')
        self.assertIn("missing required output key: answer", str(ctx.exception))

    def test_validate_output_rejects_non_object_json(self):
        tpl = MagicMock(constraint_type=1, resp_specs='[{"name":"answer"}]')

        with self.assertRaises(ValueError) as ctx:
            validate_output(tpl, '["x"]')
        self.assertIn("must be an object", str(ctx.exception))
