from django.db import models


class AiJob(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField()
    job_type = models.CharField(max_length=64)
    status = models.PositiveSmallIntegerField(default=0)  # 0 pending, 1 running, 2 done, 3 failed
    callback_url = models.CharField(max_length=1024, default="")
    payload_json = models.TextField(null=True, blank=True)
    result_json = models.TextField(null=True, blank=True)
    message = models.CharField(max_length=512, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_job"
        indexes = [
            models.Index(fields=["reg_id", "status"], name="idx_ai_job_reg_status"),
        ]
