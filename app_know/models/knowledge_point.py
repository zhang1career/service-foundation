"""
Knowledge point model (知识点): one record per sentence/knowledge point.
Renamed from Sentence. Table: knowledge. Uses batch_id to group points from same input.
"""
from django.db import models

from app_know.consts import (
    CLASS_CHOICES,
    STAGE_CREATED,
    STATUS_INCOMPLETE,
)


class KnowledgePoint(models.Model):
    """知识点：句子/知识单元，按 batch_id 分组."""

    id = models.BigAutoField(primary_key=True)
    batch_id = models.BigIntegerField(db_index=True, null=True, blank=True, help_text="同一批输入的分组 id")
    content = models.TextField()
    seq = models.IntegerField(default=0, help_text="在 batch 内的顺序，0-based")

    brief = models.TextField(blank=True, null=True)
    graph_brief = models.TextField(blank=True, null=True)
    graph_subject = models.TextField(blank=True, null=True)
    graph_object = models.TextField(blank=True, null=True)

    classification = models.CharField(max_length=32, db_index=True, blank=True, default="")
    stage = models.SmallIntegerField(db_index=True, default=STAGE_CREATED)
    status = models.SmallIntegerField(db_index=True, default=STATUS_INCOMPLETE)

    ct = models.BigIntegerField(default=0, db_index=True)
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "knowledge"
        app_label = "app_know"
        indexes = [
            models.Index(fields=["batch_id"]),
            models.Index(fields=["stage"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["batch_id", "seq"]

    def __str__(self):
        return f"KnowledgePoint(id={self.id}, batch_id={self.batch_id}, seq={self.seq})"
