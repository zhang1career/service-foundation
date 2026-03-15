"""
Batch model: one record per text submission or document upload.
Table: batch. The id corresponds to knowledge.batch_id.
source_type: 0-instant (form text), 1-file (uploaded file).
content: if source_type=0, text content; if source_type=1, file path (e.g. for OSS).
"""
from django.db import models

from app_know.consts import SOURCE_TYPE_INSTANT


class Batch(models.Model):
    """批次：每提交一段文字或每上传一个文档对应一条记录，id 对应 knowledge.batch_id"""

    id = models.BigAutoField(primary_key=True)
    content = models.TextField(blank=True, default="")
    source_type = models.SmallIntegerField(db_index=True, default=SOURCE_TYPE_INSTANT)  # 0-instant, 1-file
    ct = models.BigIntegerField(default=0, db_index=True)
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "batch"
        app_label = "app_know"
        ordering = ["-ct"]

    def __str__(self):
        st = "instant" if self.source_type == 0 else "file"
        preview = (self.content[:50] + "...") if self.content and len(self.content) > 50 else (self.content or "")
        return f"Batch(id={self.id}, content={preview!r}, source_type={st})"
