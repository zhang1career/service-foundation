from django.db import models

from app_user.enums import UserDispositionEnum, UserStatusEnum


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True, db_index=True, db_column="name")
    password_hash = models.CharField(max_length=255, db_column="pw_hash")
    email = models.CharField(max_length=255, unique=True, default="", blank=True, db_index=True)
    phone = models.CharField(max_length=32, unique=True, default="", blank=True, db_index=True)
    avatar = models.CharField(max_length=512, default="", blank=True)
    status = models.SmallIntegerField(
        choices=UserStatusEnum.choices(),
        default=UserStatusEnum.DISABLED.value,
        db_index=True,
    )
    # 认证状态：bitmask。0 表示未通过任何认证；各 bit 的含义由业务层定义。
    auth_status = models.PositiveSmallIntegerField(default=0, db_index=True, db_column="auth_status")
    ctrl_status = models.SmallIntegerField(
        choices=UserDispositionEnum.choices(),
        default=UserDispositionEnum.NONE.value,
        db_index=True,
    )
    ctrl_reason = models.CharField(max_length=512, default="", blank=True)
    ext = models.TextField(default="{}")
    ct = models.PositiveBigIntegerField(default=0, db_index=True)
    ut = models.PositiveBigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "user"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["ct"]),
        ]
