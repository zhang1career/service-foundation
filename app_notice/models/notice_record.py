from django.db import models


class NoticeRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField(db_index=True)
    event_id = models.PositiveBigIntegerField(db_index=True)
    channel = models.SmallIntegerField(db_index=True)
    target = models.CharField(max_length=255, db_index=True)
    subject = models.CharField(max_length=255, default="", blank=True)
    content = models.TextField(default="", blank=True)
    broker = models.IntegerField(default=0)
    status = models.SmallIntegerField(default=0, db_index=True)  # 1 success, 0 failed
    provider = models.CharField(max_length=64, default="", blank=True)
    message = models.CharField(max_length=255, default="", blank=True)
    ct = models.BigIntegerField(default=0, db_index=True)
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "notice"
        indexes = [
            models.Index(fields=["reg_id", "status", "ct"]),
            models.Index(fields=["event_id", "ct"]),
            models.Index(fields=["channel", "status", "ct"]),
            models.Index(fields=["target", "ct"]),
        ]
