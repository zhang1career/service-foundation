from django.db import models


class AiCallLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField(default=0)
    template_id = models.PositiveBigIntegerField(default=0)
    provider_id = models.PositiveBigIntegerField(default=0)
    model_id = models.PositiveBigIntegerField(default=0)
    latency_ms = models.IntegerField(default=0)
    success = models.SmallIntegerField(default=0)
    error_message = models.CharField(max_length=512, default="")
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "call_log"
        indexes = [
            models.Index(fields=["reg_id"], name="idx_ai_log_reg"),
        ]
