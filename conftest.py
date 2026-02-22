"""
Pytest configuration file.

This file ensures Django settings are loaded before any tests run,
which in turn loads environment variables from .env files.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_foundation.settings")
os.environ.setdefault("RUN_ENV", "test")
django.setup()

from django.conf import settings

if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")
