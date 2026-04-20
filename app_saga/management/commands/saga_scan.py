from django.core.management.base import BaseCommand

from app_saga.services.scan_service import claim_batch, process_one


class Command(BaseCommand):
    help = "Scan saga instances: advance actions and compensation retries."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        limit = int(options["limit"])
        rows = claim_batch(limit=limit)
        for inst in rows:
            process_one(inst)
