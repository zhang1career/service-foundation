from django.apps import AppConfig


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_cms"
    verbose_name = "CMS"

    def ready(self) -> None:
        import app_cms.signals  # noqa: F401
