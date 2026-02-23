"""
Django management command to create vector search index on knowledge_components.

Usage:
    python manage.py ensure_know_vector_index

Required for vector similarity search on subject/object in relation extraction.
"""
from django.core.management.base import BaseCommand

from app_know.repos import graph_node_repo


class Command(BaseCommand):
    help = "Create vector search index on knowledge_components.name_vec for relation extraction"

    def handle(self, *args, **options):
        ok = graph_node_repo.ensure_vector_index()
        if ok:
            self.stdout.write(self.style.SUCCESS("Vector index ensure completed (may already exist)"))
        else:
            self.stdout.write(self.style.WARNING("Vector index ensure failed, check logs"))
