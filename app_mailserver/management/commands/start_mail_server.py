"""
Django management command to start mail servers (SMTP and IMAP)

Usage:
    python manage.py start_mail_server
"""
import logging
import asyncio
import threading
from django.core.management.base import BaseCommand

from app_mailserver.servers.smtp_server import SMTPServer
from app_mailserver.servers.imap_server import IMAPServer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start SMTP and IMAP mail servers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--smtp-only',
            action='store_true',
            help='Start only SMTP server',
        )
        parser.add_argument(
            '--imap-only',
            action='store_true',
            help='Start only IMAP server',
        )
    
    def handle(self, *args, **options):
        """Start mail servers"""
        smtp_only = options.get('smtp_only', False)
        imap_only = options.get('imap_only', False)
        
        try:
            # Start SMTP server
            smtp_server = None
            if not imap_only:
                smtp_server = SMTPServer()
                smtp_thread = threading.Thread(target=smtp_server.start, daemon=True)
                smtp_thread.start()
                self.stdout.write(self.style.SUCCESS('SMTP server started'))
            
            # Start IMAP server
            imap_server = None
            if not smtp_only:
                imap_server = IMAPServer()
                # Run IMAP server in async event loop
                imap_thread = threading.Thread(
                    target=self._run_imap_server,
                    args=(imap_server,),
                    daemon=True
                )
                imap_thread.start()
                self.stdout.write(self.style.SUCCESS('IMAP server started'))
            
            self.stdout.write(self.style.SUCCESS('Mail servers are running. Press Ctrl+C to stop.'))
            
            # Keep main thread alive
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nStopping mail servers...'))
                if smtp_server:
                    smtp_server.stop()
                if imap_server:
                    imap_server.stop()
                self.stdout.write(self.style.SUCCESS('Mail servers stopped'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to start mail servers: {e}'))
            logger.exception("Failed to start mail servers")
            raise
    
    def _run_imap_server(self, imap_server: IMAPServer):
        """Run IMAP server in async event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(imap_server.start())
        except Exception as e:
            logger.exception(f"IMAP server error: {e}")
        finally:
            loop.close()

