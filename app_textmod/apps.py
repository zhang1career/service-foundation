from django.apps import AppConfig


class TextmodConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_textmod"

    def ready(self) -> None:
        import app_textmod.dict_registration  # noqa: F401

        from common.dict_catalog import prime_http_dict_cache

        prime_http_dict_cache()
