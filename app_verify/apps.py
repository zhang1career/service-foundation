from django.apps import AppConfig


class AppVerifyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_verify"

    def ready(self) -> None:
        import app_verify.dict_registration  # noqa: F401

        from common.dict_catalog import prime_http_dict_cache

        prime_http_dict_cache()
