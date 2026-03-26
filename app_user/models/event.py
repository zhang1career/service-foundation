from django.db import models


class Event(models.Model):
    id = models.BigAutoField(primary_key=True)
    biz_type = models.SmallIntegerField(default=0, db_index=True)
    status = models.SmallIntegerField(default=0, db_index=True)  # 0 init,1 sent,2 verified,3 completed,9 failed
    level = models.SmallIntegerField(default=3, db_index=True)
    verify_code_id = models.PositiveBigIntegerField(default=0, db_index=True)
    verify_ref_id = models.PositiveBigIntegerField(default=0, db_index=True)
    notice_target = models.CharField(max_length=255, default="", blank=True)
    notice_channel = models.SmallIntegerField(default=0, db_index=True)
    payload_json = models.TextField(default="{}")
    message = models.CharField(max_length=255, default="", blank=True)
    ct = models.PositiveBigIntegerField(default=0, db_index=True)
    ut = models.PositiveBigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "event"
        indexes = [
            models.Index(fields=["biz_type", "status", "ct"]),
            models.Index(fields=["verify_code_id"]),
        ]
