"""
Insight model: 观点生成结果（矛盾发现/路径推理/跨文本综合）.
"""
from django.db import models

from app_know.consts import (
    INSIGHT_PATH_REASONING,
    INSIGHT_TYPES,
    INSIGHT_DRAFT,
    INSIGHT_STATUS,
    PERSPECTIVE_CONCEPT,
    PERSPECTIVE_TYPES,
)


class Insight(models.Model):
    """观点：由 Insight Agent 生成的结构化洞见."""

    id = models.BigAutoField(primary_key=True)
    content = models.TextField(help_text="观点内容")
    type = models.SmallIntegerField(
        db_index=True,
        choices=INSIGHT_TYPES,
        default=INSIGHT_PATH_REASONING,
    )
    status = models.SmallIntegerField(
        db_index=True,
        choices=INSIGHT_STATUS,
        default=INSIGHT_DRAFT,
    )
    perspective = models.SmallIntegerField(
        db_index=True,
        choices=PERSPECTIVE_TYPES,
        default=PERSPECTIVE_CONCEPT,
        null=True,
        blank=True,
        help_text="视角类型 0=人物 1=概念 2=指标",
    )
    kid = models.BigIntegerField(db_index=True, null=True, blank=True, help_text="关联 knowledge.id (知识点)")
    ct = models.BigIntegerField(default=0, db_index=True)
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "insight"
        app_label = "app_know"
        ordering = ["-ut"]

    def __str__(self):
        return f"Insight(id={self.id}, type={self.type}, content={self.content[:50]!r}...)"
