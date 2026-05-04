"""
Django management command to start mail servers (SMTP and IMAP).

Delegates to :mod:`app_mailserver.runtime`. Prefer ``python -m app_mailserver`` or the
``run.sh`` / ``run_asgi.sh`` integration when running beside the web process.
"""
import logging

from django.core.management.base import BaseCommand

from app_mailserver.runtime import run_mail_servers_forever

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start SMTP and IMAP mail servers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--smtp-only",
            action="store_true",
            help="Start only SMTP server",
        )
        parser.add_argument(
            "--imap-only",
            action="store_true",
            help="Start only IMAP server",
        )

    def handle(self, *args, **options):
        smtp_only = options.get("smtp_only", False)
        imap_only = options.get("imap_only", False)

        try:
            if not imap_only:
                self.stdout.write(self.style.SUCCESS("SMTP server starting…"))
            if not smtp_only:
                self.stdout.write(self.style.SUCCESS("IMAP server starting…"))
            self.stdout.write(
                self.style.SUCCESS("Mail servers running; Ctrl+C or SIGTERM to stop.")
            )
            run_mail_servers_forever(smtp_only=smtp_only, imap_only=imap_only)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to start mail servers: {e}"))
            logger.exception("Failed to start mail servers")
            raise
