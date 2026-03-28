from django.apps import AppConfig


class CdnConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_cdn"
    label = "app_cdn"

    def ready(self) -> None:
        import app_cdn.dict_registration  # noqa: F401
