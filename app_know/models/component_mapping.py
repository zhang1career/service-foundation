"""
Knowledge-Component mapping model for MySQL storage.
Maps kid (knowledge_id) to cid (component_id in Atlas), app_id, and type (0=subject, 1=object).
Table y: knowledge-component relation.
Primary key: (kid, cid, app_id).
"""
from django.db import models


class KnowledgeComponentMapping(models.Model):
    """
    Maps a knowledge entity to its components (subject/object) in MongoDB Atlas.
    Stored in MySQL (know_rw database) for efficient querying.
    Primary key: (kid, cid, app_id).
    """

    kid = models.BigIntegerField(db_column="kid", primary_key=True)
    cid = models.CharField(max_length=255, db_column="cid")
    app_id = models.IntegerField(db_column="app_id")
    type = models.IntegerField(
        db_column="type",
        default=0,
        help_text="0=subject, 1=object",
    )

    class Meta:
        db_table = "y"
        app_label = "app_know"
        managed = False
        unique_together = [["kid", "cid", "app_id"]]

    def __str__(self):
        return f"KnowledgeComponentMapping(kid={self.kid}, cid={self.cid}, app_id={self.app_id})"
