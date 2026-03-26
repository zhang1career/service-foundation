from django.db import models


class AiProvider(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128)
    base_url = models.CharField(max_length=512)
    api_key = models.CharField(max_length=512)
    status = models.SmallIntegerField(default=1)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_provider"
        indexes = [
            models.Index(fields=["status"], name="aibroker_provider_status_idx"),
        ]
