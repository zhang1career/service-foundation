from django.apps import AppConfig


class AppNoticeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_notice"

    def ready(self) -> None:
        import app_notice.dict_registration  # noqa: F401
