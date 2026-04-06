from django.db import models

from app_user.enums.token_status_enum import TokenStatusEnum


class Token(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField(db_index=True)
    token = models.CharField(max_length=512, default="")
    refresh = models.CharField(max_length=255, default="")
    status = models.SmallIntegerField(
        default=TokenStatusEnum.INIT.value,
        db_index=True,
    )
    expires_at = models.PositiveBigIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "token"
        indexes = [
            models.Index(fields=["user_id", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "token"],
                name="uni_user_token_token",
            ),
            models.UniqueConstraint(
                fields=["user_id", "refresh"],
                name="uni_user_token_refresh",
            ),
        ]
