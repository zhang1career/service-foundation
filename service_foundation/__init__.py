import pymysql

pymysql.install_as_MySQLdb()

try:
    from .celery import app as celery_app
except ImportError:
    # Celery is optional for Django/pytest entrypoints; install celery for workers.
    celery_app = None

__all__ = ("celery_app",)
