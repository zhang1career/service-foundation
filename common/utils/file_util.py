import os

from django.conf import settings


def app_path(sub_path: str) -> str:
    return os.path.join(settings.BASE_DIR, sub_path)
