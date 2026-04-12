import logging

from django.core.management.base import BaseCommand

from app_tcc.services.scan_service import claim_batch, process_one

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scan TCC global transactions: await-confirm timeout cancel, phase retries."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        limit = int(options["limit"])
        rows = claim_batch(limit=limit)
        for g in rows:
            try:
                process_one(g)
            except Exception:
                logger.exception("tcc_scan failed tx_id=%s", g.pk)
