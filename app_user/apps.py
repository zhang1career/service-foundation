from django.apps import AppConfig


class AppUserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_user"

    def ready(self) -> None:
        import app_user.dict_registration  # noqa: F401

        from django.conf import settings

        if not getattr(settings, "APP_VERIFY_ENABLED", True):
            from common.dict_catalog import prime_http_dict_cache

            prime_http_dict_cache()
