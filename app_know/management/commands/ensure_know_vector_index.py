"""
Django management command to create vector search indexes for app_know.

Usage:
    python manage.py ensure_know_vector_index

Creates:
- sentence_raw.content_vec for sentence semantic search

Note: knowledge_summaries and knowledge_components are disabled (Atlas account limits).
"""
from django.core.management.base import BaseCommand

from app_know.repos.sentence_raw_repo import ensure_sentence_raw_vector_index


class Command(BaseCommand):
    help = "Create vector search indexes for sentence_raw (knowledge_summaries, knowledge_components disabled)"

    def handle(self, *args, **options):
        ok_sentence_raw = ensure_sentence_raw_vector_index()
        if ok_sentence_raw:
            self.stdout.write(self.style.SUCCESS("Sentence_raw vector index: ok (may already exist)"))
        else:
            self.stdout.write(self.style.WARNING("Sentence_raw vector index: failed, check logs"))
        self.stdout.write("knowledge_summaries, knowledge_components: skipped (disabled due to Atlas limits)")
