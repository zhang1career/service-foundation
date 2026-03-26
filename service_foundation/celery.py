import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_foundation.settings")

app = Celery("service_foundation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(packages=["common"])
