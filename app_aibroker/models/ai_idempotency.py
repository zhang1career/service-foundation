from django.db import models


class AiIdempotency(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField()
    idem_key = models.CharField(max_length=128)
    req_hash = models.CharField(max_length=64, default="")
    resp_json = models.TextField()
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_idem"
        constraints = [
            models.UniqueConstraint(
                fields=["reg_id", "idem_key"],
                name="aibroker_idem_reg_key_uniq",
            ),
        ]
