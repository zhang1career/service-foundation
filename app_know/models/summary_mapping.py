"""
Knowledge-Summary mapping model for MySQL storage.
Maps kid (knowledge_id) to sid (summary_id in MongoDB) and app_id.
"""
from django.db import models


class KnowledgeSummaryMapping(models.Model):
    """
    Maps a knowledge entity to its summary in MongoDB Atlas.
    Stored in MySQL (know_rw database) for efficient querying.
    Primary key: (kid, app_id) composite key.
    """

    kid = models.BigIntegerField(db_column="kid")
    app_id = models.CharField(max_length=128, db_column="app_id")
    sid = models.CharField(max_length=64, db_column="sid", db_index=True)

    class Meta:
        db_table = "x"
        app_label = "app_know"
        managed = False
        indexes = [
            models.Index(fields=["sid"]),
        ]

    def __str__(self):
        return f"KnowledgeSummaryMapping(kid={self.kid}, app_id={self.app_id}, sid={self.sid})"
