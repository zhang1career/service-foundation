"""
Knowledge entity model for MySQL-backed knowledge storage.
Generated.
"""
from django.db import models

from common.consts.string_const import EMPTY_STRING


class Knowledge(models.Model):
    """Knowledge entity stored in know_rw MySQL."""

    id = models.BigAutoField(primary_key=True)

    # Human-readable title
    title = models.CharField(max_length=512, db_index=True)
    # Optional description
    description = models.TextField(blank=True, null=True)
    # Knowledge content (main body text)
    content = models.TextField(blank=True, null=True)
    # Source type (e.g. 'document', 'url', 'ingestion')
    source_type = models.CharField(max_length=64, db_index=True, default=EMPTY_STRING)

    # Create time (Unix timestamp, milliseconds)
    ct = models.BigIntegerField(default=0, db_index=True)
    # Update time (Unix timestamp, milliseconds)
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "knowledge"
        app_label = "app_know"
        indexes = [
            models.Index(fields=["source_type"]),
            models.Index(fields=["ct"]),
            models.Index(fields=["ut"]),
        ]

    def __str__(self):
        return f"Knowledge(id={self.id}, title={self.title!r})"
