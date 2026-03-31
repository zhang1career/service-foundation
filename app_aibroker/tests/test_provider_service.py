from unittest import TestCase
from unittest.mock import MagicMock, patch

from app_aibroker.services.provider_service import ModelService, ProviderService


class ProviderServiceTest(TestCase):
    def test_create_by_payload_requires_mandatory_fields(self):
        with self.assertRaises(ValueError) as ctx:
            ProviderService.create_by_payload({"name": "n"})
        self.assertIn("required", str(ctx.exception))

    @patch("app_aibroker.services.provider_service.create_provider")
    def test_create_by_payload_strips_url_fields(self, create_provider_mock):
        provider = MagicMock(
            id=1,
            name="x",
            base_url="https://api.example.com",
            url_path="/v1/chat",
            status=1,
            ct=1,
            ut=2,
        )
        create_provider_mock.return_value = provider

        out = ProviderService.create_by_payload(
            {
                "name": "x",
                "base_url": " https://api.example.com ",
                "api_key": "k",
                "url_path": " /v1/chat ",
            }
        )

        self.assertEqual(out["id"], 1)
        create_provider_mock.assert_called_once_with(
            "x", "https://api.example.com", "k", "/v1/chat", status=1
        )

    @patch("app_aibroker.services.provider_service.update_provider")
    def test_update_by_payload_provider_not_found(self, update_provider_mock):
        update_provider_mock.return_value = None

        with self.assertRaises(ValueError) as ctx:
            ProviderService.update_by_payload(7, {"name": "n"})
        self.assertEqual(str(ctx.exception), "provider not found")


class ModelServiceTest(TestCase):
    @patch("app_aibroker.repos.create_model")
    @patch("app_aibroker.services.provider_service.validate_ai_model_param_specs_json")
    def test_create_by_payload_with_param_specs(
        self, validate_mock, create_model_mock
    ):
        validate_mock.return_value = None
        model = MagicMock(
            id=2,
            provider_id=1,
            model_name="gpt-4o-mini",
            capability=0,
            status=1,
            param_specs='[{"n":"temperature","t":"FLOAT"}]',
            ct=3,
            ut=4,
        )
        create_model_mock.return_value = model

        out = ModelService.create_by_payload(
            {
                "provider_id": 1,
                "model_name": "gpt-4o-mini",
                "param_specs": ' [{"n":"temperature","t":"FLOAT"}] ',
            }
        )

        self.assertEqual(out["id"], 2)
        validate_mock.assert_called_once_with('[{"n":"temperature","t":"FLOAT"}]')
        create_model_mock.assert_called_once()
        args, kwargs = create_model_mock.call_args
        self.assertEqual(args[0], 1)
        self.assertEqual(args[1], "gpt-4o-mini")
        self.assertEqual(kwargs["param_specs"], '[{"n":"temperature","t":"FLOAT"}]')

    @patch("app_aibroker.repos.get_model_by_id")
    @patch("app_aibroker.repos.update_model")
    @patch("app_aibroker.services.provider_service.validate_ai_model_param_specs_json")
    def test_update_rejects_invalid_param_specs(
        self, validate_mock, _update_model_mock, get_model_by_id_mock
    ):
        get_model_by_id_mock.return_value = MagicMock(id=1)
        validate_mock.return_value = "bad specs"

        with self.assertRaises(ValueError) as ctx:
            ModelService.update(1, {"param_specs": "[]"})
        self.assertEqual(str(ctx.exception), "bad specs")
