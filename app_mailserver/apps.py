from django.apps import AppConfig


class MailserverConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_mailserver"
    label = "app_mailserver"

    def ready(self) -> None:
        import app_mailserver.dict_registration  # noqa: F401
