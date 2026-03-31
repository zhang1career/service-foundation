"""AI Broker 模型列表：入参 object_array 场景下的渲染与 POST（需先 stub openai，避免加载 urlconf 时拉取 pydantic/openai 链失败）。"""
import json
import sys
import types

if "openai" not in sys.modules:
    _openai_stub = types.ModuleType("openai")
    _openai_stub.OpenAI = object
    sys.modules["openai"] = _openai_stub

from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.test.client import MULTIPART_CONTENT
from django.template.loader import render_to_string

from app_console.utils import embed_dict_as_json_script_body
from app_console.views.aibroker_view import AibrokerModelConsoleView


_OBJECT_ARRAY_SPECS = (
    '[{"n":"messages","t":"OBJECT_ARRAY","r":{},'
    '"c":[{"n":"role","t":"STRING","r":{}},'
    '{"n":"content","t":"STRING","r":{}}]}]'
)


@override_settings(
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies",
)
class AibrokerModelConsoleRenderTest(SimpleTestCase):
    def _session_request(self, path: str):
        rf = RequestFactory()
        request = rf.get(path)
        request.user = AnonymousUser()
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        return request

    def test_embed_dict_accepts_bytes_like_param_specs(self):
        b = embed_dict_as_json_script_body({1: _OBJECT_ARRAY_SPECS.encode("utf-8")})
        outer = json.loads(str(b))
        self.assertEqual(outer["1"], _OBJECT_ARRAY_SPECS)

    def test_get_context_and_render_models_template_with_object_array(self):
        request = self._session_request("/console/aibroker/providers/1/models/")
        view = AibrokerModelConsoleView()
        view.setup(request, provider_id=1)
        with patch(
            "app_console.views.aibroker_view.ProviderService.get_one",
            return_value={"id": 1, "name": "P"},
        ), patch(
            "app_console.views.aibroker_view.ModelService.list_for_provider",
            return_value=[
                {
                    "id": 7,
                    "provider_id": 1,
                    "model_name": "gpt-4",
                    "capability": 0,
                    "status": 1,
                    "param_specs": _OBJECT_ARRAY_SPECS,
                    "ct": 0,
                    "ut": 0,
                },
            ],
        ), patch(
            "app_console.views.aibroker_view.get_dict_by_codes",
            return_value={
                "aibroker_model_capability": [{"k": "对话", "v": "0"}],
            },
        ):
            ctx = view.get_context_data(provider_id=1)
        html = render_to_string("console/aibroker/models.html", ctx, request=request)
        self.assertIn("aibroker-model-param-specs", html)
        part = html.split('id="aibroker-model-param-specs"', 1)[1]
        part = part.split("</script>", 1)[0]
        blob = part.split(">", 1)[1].strip()
        outer = json.loads(blob)
        self.assertEqual(outer["7"], _OBJECT_ARRAY_SPECS)

    def test_post_update_multipart_calls_model_service_with_param_specs(self):
        request = RequestFactory().post(
            "/console/aibroker/providers/1/models/",
            data={
                "action": "update",
                "model_id": "7",
                "model_name": "gpt-4",
                "capability": "0",
                "param_specs": _OBJECT_ARRAY_SPECS,
            },
            content_type=MULTIPART_CONTENT,
        )
        request.user = AnonymousUser()
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        request._dont_enforce_csrf_checks = True

        view = AibrokerModelConsoleView.as_view()
        with patch(
            "app_console.views.aibroker_view.ProviderService.get_one",
            return_value={"id": 1},
        ) as gp, patch(
            "app_console.views.aibroker_view.ModelService.update",
            return_value={"id": 7},
        ) as mu:
            response = view(request, provider_id=1)
        self.assertEqual(response.status_code, 302)
        gp.assert_called_once_with(1)
        mu.assert_called_once()
        args, kwargs = mu.call_args
        self.assertEqual(args[0], 7)
        self.assertEqual(args[1]["param_specs"], _OBJECT_ARRAY_SPECS)
