"""
Run mail servers as a standalone process::

    python -m app_mailserver
    python -m app_mailserver --smtp-only
    python -m app_mailserver --imap-only

Requires ``DJANGO_SETTINGS_MODULE`` (defaults to ``service_foundation.settings``).
Exits immediately when ``APP_MAILSERVER_ENABLED`` is false.
"""

from __future__ import annotations

import logging
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service_foundation.settings")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger(__name__)

    import django

    django.setup()

    from django.conf import settings

    if not getattr(settings, "APP_MAILSERVER_ENABLED", False):
        log.info("APP_MAILSERVER_ENABLED is false; mail subprocess exiting.")
        return

    smtp_only = "--smtp-only" in sys.argv
    imap_only = "--imap-only" in sys.argv

    from app_mailserver.runtime import run_mail_servers_forever

    run_mail_servers_forever(smtp_only=smtp_only, imap_only=imap_only)


if __name__ == "__main__":
    main()
