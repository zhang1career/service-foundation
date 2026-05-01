"""
SMTP/IMAP process entrypoint used by ``python -m app_mailserver`` and ``manage.py start_mail_server``.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import threading
import time

logger = logging.getLogger(__name__)


def _run_imap_server(imap_server) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(imap_server.start())
    except Exception as e:
        logger.exception("IMAP server error: %s", e)
    finally:
        loop.close()


def run_mail_servers_forever(*, smtp_only: bool = False, imap_only: bool = False) -> None:
    """
    Start SMTP and/or IMAP and block until SIGTERM/SIGINT.

    Runs IMAP in a dedicated thread with its own asyncio loop (same layout as the
    historical management command).
    """
    smtp_server = None
    imap_server = None
    shutdown = threading.Event()

    def _stop_servers() -> None:
        if smtp_server:
            try:
                smtp_server.stop()
            except Exception:
                logger.exception("Error stopping SMTP server")
        if imap_server:
            try:
                imap_server.stop()
            except Exception:
                logger.exception("Error stopping IMAP server")

    def _handle_signal(signum: int, _frame: object | None) -> None:
        logger.info("Mail servers received signal %s; stopping...", signum)
        _stop_servers()
        shutdown.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        from app_mailserver.servers.imap_server import IMAPServer
        from app_mailserver.servers.smtp_server import SMTPServer

        if not imap_only:
            smtp_server = SMTPServer()
            threading.Thread(target=smtp_server.start, daemon=True).start()
            logger.info("SMTP server thread started")

        if not smtp_only:
            imap_server = IMAPServer()
            threading.Thread(
                target=_run_imap_server,
                args=(imap_server,),
                daemon=True,
            ).start()
            logger.info("IMAP server thread started")

        while not shutdown.wait(timeout=1.0):
            pass
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt; stopping mail servers...")
        _stop_servers()
        shutdown.set()
