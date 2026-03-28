import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch

if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.services.text_generation_service import generate_text


class TextGenerationServiceTest(TestCase):
    @patch("app_aibroker.services.text_generation_service.create_call_log")
    @patch("app_aibroker.services.text_generation_service.chat_completion")
    @patch("app_aibroker.services.text_generation_service.default_chat_model")
    @patch("app_aibroker.services.text_generation_service.get_template")
    def test_generate_text_resolves_prompt_by_template_id(
        self, get_template_mock, dcm_mock, chat_mock, _log_mock
    ):
        provider = MagicMock(id=10)
        model = MagicMock(id=20, capability=ModelCapabilityEnum.CHAT, status=1)
        dcm_mock.return_value = (provider, model)
        tpl = MagicMock()
        tpl.id = 5
        tpl.status = 1
        tpl.body = "Hello {name}"
        tpl.constraint_type = 0
        tpl.output_variables = None
        get_template_mock.return_value = tpl
        chat_mock.return_value = " out "

        reg = MagicMock()
        reg.id = 1
        result, err = generate_text(
            reg,
            {"template_id": 5, "variables": {"name": "world"}},
            idempotency_key=None,
        )
        self.assertIsNone(err)
        self.assertEqual((result.get("text") or "").strip(), "out")
        self.assertEqual(result.get("template_id"), 5)
        chat_mock.assert_called_once()
        args, kwargs = chat_mock.call_args
        self.assertEqual(args[2], "Hello world")

    def test_generate_text_rejects_template_key_and_template_id_together(self):
        reg = MagicMock()
        reg.id = 1
        result, err = generate_text(
            reg,
            {"template_key": "k", "template_id": 1, "prompt": ""},
            idempotency_key=None,
        )
        self.assertEqual(result, {})
        self.assertEqual(err, "use only one of template_key or template_id")

    @patch("app_aibroker.services.text_generation_service.get_template")
    def test_generate_text_template_id_not_found(self, get_template_mock):
        get_template_mock.return_value = None
        reg = MagicMock()
        reg.id = 1
        result, err = generate_text(reg, {"template_id": 99}, idempotency_key=None)
        self.assertEqual(result, {})
        self.assertEqual(err, "template not found or inactive")
