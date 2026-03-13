#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_foundation.settings")

    # Load .env (and .env.prod etc.) before runserver so HOST/PORT take effect
    from common.utils.env_util import load_env

    base_dir = Path(__file__).resolve().parent
    load_env(base_dir)

    # For runserver: inject HOST:PORT from env if no addrport given
    if "runserver" in sys.argv:
        runserver_idx = sys.argv.index("runserver")
        # Check if addrport already provided (next arg exists and is not an option)
        has_addrport = (
            runserver_idx + 1 < len(sys.argv)
            and not sys.argv[runserver_idx + 1].startswith("-")
        )
        if not has_addrport:
            host = os.environ.get("HOST", "127.0.0.1")
            port = os.environ.get("PORT", "8000")
            sys.argv.insert(runserver_idx + 1, f"{host}:{port}")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
