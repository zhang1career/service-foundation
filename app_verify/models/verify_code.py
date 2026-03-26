from django.db import models
from app_verify.enums import VerifyLevelEnum


class VerifyCode(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.SmallIntegerField(
        choices=[(item.value, item.name) for item in VerifyLevelEnum],
        db_index=True,
        default=VerifyLevelEnum.PASS.value,
    )
    code = models.CharField(max_length=16)
    reg_id = models.PositiveBigIntegerField(db_index=True)
    ref_id = models.BigIntegerField(db_index=True)
    expires_at = models.PositiveBigIntegerField(db_index=True)
    used_at = models.PositiveBigIntegerField(default=0, db_index=True)
    ct = models.PositiveBigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "verify_code"
        indexes = [
            models.Index(fields=["reg_id", "level", "ct"]),
            models.Index(fields=["ref_id", "level"]),
        ]
