from django.db import models

from app_verify.enums import VerifyLogActionEnum


class VerifyLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField(db_index=True, default=0)
    ref_id = models.BigIntegerField(default=0, db_index=True)
    code_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    level = models.SmallIntegerField(default=0, db_index=True)
    action = models.SmallIntegerField(
        choices=[(item.value, item.name) for item in VerifyLogActionEnum],
        db_index=True,
    )
    ok = models.SmallIntegerField(default=1, db_index=True)
    message = models.CharField(max_length=512, default="")
    ct = models.PositiveBigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "verify_log"
        indexes = [
            models.Index(fields=["reg_id", "ct"]),
            models.Index(fields=["code_id", "ct"]),
        ]
