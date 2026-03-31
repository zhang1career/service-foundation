import sys
import types
from unittest import TestCase
from unittest.mock import MagicMock, patch

if "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = object
    sys.modules["openai"] = openai_stub

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from app_aibroker.services.text_generation_service import (
    _apply_model_param_placeholders,
    _coerce_model_params,
    _flatten_ai_model_param_specs_for_coerce,
    _load_ai_model_param_specs_tree,
    _merge_model_param_defaults,
    generate_text,
)


def _specs_for_coerce(raw: str):
    return _flatten_ai_model_param_specs_for_coerce(_load_ai_model_param_specs_tree(raw))


class TextGenerationServiceTest(TestCase):
    def test_parse_and_coerce_model_params(self):
        specs = _specs_for_coerce(
            '[{"n":"max_tokens","t":"INT","r":{"min":1,"max":100}},'
            '{"n":"mode","t":"ENUM","r":{"values":["a","b"]}}]'
        )
        self.assertEqual(len(specs), 2)
        coerced, err = _coerce_model_params({"max_tokens": "50", "mode": "a"}, specs)
        self.assertIsNone(err)
        self.assertEqual(coerced["max_tokens"], 50)
        self.assertEqual(coerced["mode"], "a")

    def test_coerce_nested_object_specs(self):
        specs = _specs_for_coerce(
            '[{"n":"outer","t":"OBJECT","r":{},'
            '"c":[{"n":"inner","t":"INT","r":{"min":1,"max":10}}]}]'
        )
        self.assertEqual([s["name"] for s in specs], ["outer.inner"])
        coerced, err = _coerce_model_params({"outer": {"inner": "5"}}, specs)
        self.assertIsNone(err)
        self.assertEqual(coerced, {"outer": {"inner": 5}})

    def test_coerce_model_params_rejects_unknown_keys(self):
        specs = _specs_for_coerce('[{"n":"x","t":"STRING","r":{}}]')
        coerced, err = _coerce_model_params({"x": "ok", "y": "no"}, specs)
        self.assertIsNone(err)
        self.assertEqual(coerced, {"x": "ok"})

    def test_merge_model_param_defaults_literal(self):
        specs = _specs_for_coerce(
            '[{"n":"p","t":"STRING","r":{},"default":"fixed"}]'
        )
        merged = _merge_model_param_defaults({}, specs)
        self.assertEqual(merged, {"p": "fixed"})
        coerced, err = _coerce_model_params(merged, specs)
        self.assertIsNone(err)
        self.assertEqual(coerced["p"], "fixed")

    def test_merge_model_param_defaults_skips_when_request_sent(self):
        specs = _specs_for_coerce(
            '[{"n":"p","t":"STRING","r":{},"default":"x"}]'
        )
        merged = _merge_model_param_defaults({"p": "from_client"}, specs)
        self.assertEqual(merged["p"], "from_client")

    def test_coerce_model_params_array(self):
        specs = _specs_for_coerce(
            '[{"n":"tags","t":"ARRAY","r":{}}]'
        )
        coerced, err = _coerce_model_params({"tags": "[1,2]"}, specs)
        self.assertIsNone(err)
        self.assertEqual(coerced["tags"], [1, 2])
        coerced2, err2 = _coerce_model_params({"tags": ["a", "b"]}, specs)
        self.assertIsNone(err2)
        self.assertEqual(coerced2["tags"], ["a", "b"])

    def test_coerce_model_params_object_array(self):
        specs = _specs_for_coerce(
            '[{"n":"tools","t":"OBJECT_ARRAY","r":{}}]'
        )
        coerced, err = _coerce_model_params(
            {"tools": '[{"type":"function"}]'}, specs
        )
        self.assertIsNone(err)
        self.assertEqual(coerced["tools"], [{"type": "function"}])
        _, err2 = _coerce_model_params({"tools": "[1]"}, specs)
        self.assertIsNotNone(err2)

    def test_flatten_object_array_nested_children(self):
        specs = _specs_for_coerce(
            '[{"n":"items","t":"OBJECT_ARRAY","r":{},'
            '"c":[{"n":"id","t":"INT","r":{}}]}]'
        )
        self.assertEqual([s["name"] for s in specs], ["items.id"])

    def test_content_placeholder_injects_resolved_user_message(self):
        specs = _specs_for_coerce(
            '[{"n":"prompt_text","t":"STRING","r":{},"x":"content"}]'
        )
        api = {"max_tokens": 10}
        raw = {"content": "client_should_not_win"}
        _apply_model_param_placeholders(api, specs, raw, "rendered prompt")
        self.assertEqual(api["max_tokens"], 10)
        self.assertEqual(api["prompt_text"], "rendered prompt")

    def test_content_placeholder_nested_path(self):
        specs = _specs_for_coerce(
            '[{"n":"root","t":"OBJECT","r":{},'
            '"c":[{"n":"inner","t":"STRING","r":{},"x":"content"}]}]'
        )
        api: dict = {}
        _apply_model_param_placeholders(api, specs, {}, [{"type": "text", "text": "m"}])
        self.assertEqual(api["root"]["inner"], [{"type": "text", "text": "m"}])

    def test_placeholder_matches_any_top_level_model_params_key(self):
        specs = _specs_for_coerce(
            '[{"n":"leaf","t":"STRING","r":{},"x":"myvar"}]'
        )
        raw = {"leaf": "coerced_before", "myvar": "from_alias"}
        merged = _merge_model_param_defaults(raw, specs)
        coerced, err = _coerce_model_params(merged, specs)
        self.assertIsNone(err)
        ph_err = _apply_model_param_placeholders(coerced, specs, raw, "uc")
        self.assertIsNone(ph_err)
        self.assertEqual(coerced.get("leaf"), "from_alias")

    def test_placeholder_alias_uses_spec_type_coercion(self):
        specs = _specs_for_coerce(
            '[{"n":"dimensions","t":"INT","r":{},"x":"dim"}]'
        )
        raw = {"dim": "384"}
        merged = _merge_model_param_defaults(raw, specs)
        coerced, err = _coerce_model_params(merged, specs)
        self.assertIsNone(err)
        ph_err = _apply_model_param_placeholders(coerced, specs, raw, "uc")
        self.assertIsNone(ph_err)
        self.assertEqual(coerced.get("dimensions"), 384)

    @patch("app_aibroker.services.text_generation_service.request_sync")
    def test_placeholder_alias_image_downloads_url_to_base64(self, request_sync_mock):
        specs = _specs_for_coerce(
            '[{"n":"image","t":"STRING","r":{},"x":"image"}]'
        )
        raw = {"image": "https://oss.example.com/a.png"}
        merged = _merge_model_param_defaults(raw, specs)
        coerced, err = _coerce_model_params(merged, specs)
        self.assertIsNone(err)
        request_sync_mock.return_value = MagicMock(status_code=200, content=b"\x89PNG")

        ph_err = _apply_model_param_placeholders(coerced, specs, raw, "uc")
        self.assertIsNone(ph_err)
        self.assertEqual(coerced.get("image"), "iVBORw==")

    @patch("app_aibroker.services.text_generation_service.create_call_log")
    @patch("app_aibroker.services.text_generation_service.chat_completion")
    @patch("app_aibroker.services.text_generation_service.get_template")
    def test_generate_text_merged_default_role_under_messages_reaches_invoke(
        self, get_template_mock, chat_mock, _log_mock
    ):
        """param_specs OBJECT ``messages`` with default ``role`` is merged before coerce and sent as request body."""
        provider = MagicMock(id=10)
        model = MagicMock(
            id=20,
            provider_id=10,
            capability=ModelCapabilityEnum.CHAT,
            status=1,
            param_specs=(
                '[{"n":"messages","t":"OBJECT","r":{},'
                '"c":['
                '{"n":"role","t":"STRING","r":{},"default":"user"},'
                '{"n":"text","t":"STRING","r":{},"x":"content"}'
                "]}]"
            ),
        )
        tpl = MagicMock()
        tpl.id = 5
        tpl.status = 1
        tpl.body = "Hi"
        tpl.constraint_type = 0
        tpl.resp_specs = None
        tpl.param_specs = ""
        get_template_mock.return_value = tpl
        chat_mock.return_value = "ok"

        with patch(
            "app_aibroker.services.text_generation_service.get_model_by_id",
            return_value=model,
        ):
            with patch(
                "app_aibroker.services.text_generation_service.get_provider_by_id",
                return_value=provider,
            ):
                reg = MagicMock()
                reg.id = 1
                result, err = generate_text(
                    reg,
                    {"template_id": 5, "variables": {}, "model_id": 20},
                    idempotency_key=None,
                )
        self.assertIsNone(err)
        self.assertEqual((result.get("text") or "").strip(), "ok")
        chat_mock.assert_called_once()
        body = chat_mock.call_args[0][2]
        self.assertEqual(body["messages"]["role"], "user")
        self.assertEqual(body["messages"]["text"], "Hi")
        self.assertEqual(body["temperature"], 0.7)

    @patch("app_aibroker.services.text_generation_service.create_call_log")
    @patch("app_aibroker.services.text_generation_service.chat_completion")
    @patch("app_aibroker.services.text_generation_service.default_chat_model")
    @patch("app_aibroker.services.text_generation_service.get_template")
    def test_generate_text_resolves_prompt_by_template_id(
        self, get_template_mock, dcm_mock, chat_mock, _log_mock
    ):
        provider = MagicMock(id=10)
        model = MagicMock(id=20, capability=ModelCapabilityEnum.CHAT, status=1)
        model.param_specs = ""
        dcm_mock.return_value = (provider, model)
        tpl = MagicMock()
        tpl.id = 5
        tpl.status = 1
        tpl.body = "Hello {name}"
        tpl.constraint_type = 0
        tpl.resp_specs = None
        tpl.param_specs = ""
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
        args, _kwargs = chat_mock.call_args
        body = args[2]
        self.assertEqual(body["messages"][0]["content"], "Hello world")
        self.assertEqual(body["temperature"], 0.7)

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
