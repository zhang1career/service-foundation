import time
from decimal import Decimal

from django.db import models

from app_searchrec.enums import SearchRecEventType


def _now_ms() -> int:
    return int(time.time() * 1000)


class SearchRecReg(models.Model):
    """使用方（调用方）注册表 sf_searchrec.reg。"""

    name = models.CharField(max_length=128)
    access_key = models.CharField(max_length=64)
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_searchrec"
        db_table = "reg"
        constraints = [
            models.UniqueConstraint(fields=["access_key"], name="searchrec_reg_access_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["name"], name="searchrec_reg_name_idx"),
            models.Index(fields=["status"], name="searchrec_reg_status_idx"),
        ]


class SearchRecDocument(models.Model):
    rid = models.ForeignKey(
        SearchRecReg,
        on_delete=models.PROTECT,
        db_column="rid",
        related_name="documents",
    )
    # max_length=191: utf8mb4 index prefix ≤767 bytes in older InnoDB (≈191 chars); see Django MySQL notes.
    doc_key = models.CharField(max_length=191)
    title = models.CharField(max_length=512)
    content = models.TextField()
    tags = models.TextField(default="")
    # sum(tf^2); tf are integers => exact integer; BIGINT avoids float drift
    lexical_norm_sq = models.BigIntegerField(default=0)
    score_boost = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("1.00")
    )
    ct = models.BigIntegerField()
    ut = models.BigIntegerField()

    class Meta:
        app_label = "app_searchrec"
        db_table = "doc"
        constraints = [
            models.UniqueConstraint(fields=["rid", "doc_key"], name="uniq_searchrec_doc_rid_key"),
        ]
        indexes = [
            models.Index(fields=["rid"], name="idx_searchrec_doc_rid"),
        ]

    def save(self, *args, **kwargs):
        now = _now_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class SearchRecDocTerm(models.Model):
    """Inverted index rows: term -> doc_key with within-document term frequency."""

    rid = models.ForeignKey(
        SearchRecReg,
        on_delete=models.PROTECT,
        db_column="rid",
        related_name="doc_terms",
    )
    doc_key = models.CharField(max_length=191)
    term = models.CharField(max_length=191)
    tf = models.PositiveIntegerField(default=1)

    class Meta:
        app_label = "app_searchrec"
        db_table = "doc_term"
        constraints = [
            models.UniqueConstraint(
                fields=["rid", "doc_key", "term"],
                name="uniq_searchrec_doc_term_rid",
            ),
        ]
        indexes = [
            models.Index(fields=["rid", "term"], name="idx_doc_term_rid_term"),
        ]


class SearchRecEvent(models.Model):
    rid = models.ForeignKey(
        SearchRecReg,
        on_delete=models.PROTECT,
        db_column="rid",
        related_name="events",
    )
    uid = models.BigIntegerField(null=True, blank=True)
    did = models.CharField(max_length=128, null=True, blank=True)
    event_type = models.IntegerField(choices=SearchRecEventType.choices)
    payload = models.TextField(default="{}")
    ct = models.BigIntegerField()

    class Meta:
        app_label = "app_searchrec"
        db_table = "event"
        indexes = [
            models.Index(fields=["rid", "event_type", "ct"], name="idx_event_rid_type_ct"),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.ct = _now_ms()
        super().save(*args, **kwargs)
