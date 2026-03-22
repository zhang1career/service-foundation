"""
Knowledge point model (知识点): one record per sentence/knowledge point.
Renamed from Sentence. Table: knowledge. Uses batch_id to group points from same input.
"""
from django.db import models

from app_know.enums.classification_enum import ClassificationEnum
from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
from app_know.enums.stage_enum import StageEnum


class KnowledgePoint(models.Model):
    """知识点：句子/知识单元，按 batch_id 分组."""

    id = models.BigAutoField(primary_key=True)
    batch_id = models.BigIntegerField(db_index=True, null=True, blank=True, help_text="同一批输入的分组 id")
    content = models.TextField()
    seq = models.IntegerField(default=0, help_text="在 batch 内的顺序，0-based")

    brief = models.TextField(blank=True, null=True)
    graph_brief = models.TextField(blank=True, null=True, db_column="g_brief")
    graph_subject = models.TextField(blank=True, null=True, db_column="g_sub")
    graph_object = models.TextField(blank=True, null=True, db_column="g_obj")
    vec_sub_deco_id = models.CharField(max_length=32, blank=True, null=True,
                                       help_text="Mongo Atlas sub_deco collection document _id for vector update",
                                       db_column="v_sub_deco_id")
    vec_obj_deco_id = models.CharField(max_length=32, blank=True, null=True,
                                       help_text="Mongo Atlas obj_deco collection document _id for vector update",
                                       db_column="v_obj_deco_id")
    graph_brief_hash = models.IntegerField(null=True, blank=True, db_index=True, db_column="g_brief_hash")
    graph_subject_hash = models.IntegerField(null=True, blank=True, db_index=True, db_column="g_sub_hash")
    graph_object_hash = models.IntegerField(null=True, blank=True, db_index=True, db_column="g_obj_hash")

    classification = models.SmallIntegerField(db_index=True, default=ClassificationEnum.FACT)
    stage = models.SmallIntegerField(db_index=True, default=StageEnum.CREATE)  # 0=已创建
    status = models.SmallIntegerField(db_index=True, default=KnowledgeStatusEnum.INCOMPLETE)

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
