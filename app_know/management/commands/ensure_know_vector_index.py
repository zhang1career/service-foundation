"""
Django management command to create vector search indexes for app_know.

Usage:
    python manage.py ensure_know_vector_index

Creates:
- knowledge_components.name_vec (with app_id filter) for relation extraction
- knowledge_summaries.summary_vec (with app_id filter) for summary semantic search

Note: If indexes already exist without the app_id filter, drop them in Atlas UI
first, then run this command again.
"""
from django.core.management.base import BaseCommand

from app_know.repos import component_repo, summary_repo


class Command(BaseCommand):
    help = "Create vector search indexes for knowledge_components and knowledge_summaries"

    def handle(self, *args, **options):
        ok_component = component_repo.ensure_vector_index()
        ok_summary = summary_repo.ensure_summary_vector_index()
        if ok_component:
            self.stdout.write(self.style.SUCCESS("Component vector index: ok (may already exist)"))
        else:
            self.stdout.write(self.style.WARNING("Component vector index: failed, check logs"))
        if ok_summary:
            self.stdout.write(self.style.SUCCESS("Summary vector index: ok (may already exist)"))
        else:
            self.stdout.write(self.style.WARNING("Summary vector index: failed, check logs"))
