import time
from decimal import Decimal

from django.db import models

from app_searchrec.enums import SearchRecEventType


def _now_ms() -> int:
    return int(time.time() * 1000)


class SearchRecDocument(models.Model):
    biz_doc_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=512)
    content = models.TextField()
    tags = models.TextField(default="")
    score_boost = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("1.00")
    )
    ct = models.BigIntegerField()
    ut = models.BigIntegerField()

    class Meta:
        app_label = "app_searchrec"
        db_table = "doc"

    def save(self, *args, **kwargs):
        now = _now_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class SearchRecEvent(models.Model):
    uid = models.BigIntegerField(null=True, blank=True)
    did = models.CharField(max_length=128, null=True, blank=True)
    event_type = models.IntegerField(choices=SearchRecEventType.choices)
    payload = models.TextField(default="{}")
    ct = models.BigIntegerField()

    class Meta:
        app_label = "app_searchrec"
        db_table = "event"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.ct = _now_ms()
        super().save(*args, **kwargs)
