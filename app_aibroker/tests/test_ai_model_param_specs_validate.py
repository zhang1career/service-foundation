from unittest import TestCase

from app_aibroker.services.ai_model_param_specs_validate import (
    validate_ai_model_param_specs_json,
)
from app_aibroker.services.provider_service import ModelService


class AiModelParamSpecsValidateTest(TestCase):
    def test_blank_ok(self):
        self.assertIsNone(validate_ai_model_param_specs_json(""))
        self.assertIsNone(validate_ai_model_param_specs_json("  "))

    def test_invalid_json(self):
        err = validate_ai_model_param_specs_json("{")
        self.assertIn("valid JSON", err or "")

    def test_model_service_create_rejects_invalid_specs(self):
        with self.assertRaises(ValueError) as ctx:
            ModelService.create_by_payload(
                {
                    "provider_id": 1,
                    "model_name": "m",
                    "param_specs": '{"not":"array"}',
                }
            )
        self.assertIn("array", str(ctx.exception))

    def test_model_service_create_accepts_nested_wire(self):
        from unittest.mock import patch

        specs = (
            '[{"n":"o","t":"OBJECT","r":{},'
            '"c":[{"n":"x","t":"STRING","r":{}}]}]'
        )
        with patch("app_aibroker.repos.model_repo.create_model") as cm:
            cm.return_value = type(
                "M",
                (),
                {
                    "id": 1,
                    "provider_id": 1,
                    "model_name": "m",
                    "capability": 0,
                    "status": 1,
                    "param_specs": specs,
                    "ct": 0,
                    "ut": 0,
                },
            )()
            ModelService.create_by_payload(
                {
                    "provider_id": 1,
                    "model_name": "m",
                    "param_specs": specs,
                }
            )
        cm.assert_called_once()
