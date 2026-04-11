from django.db import models

from app_keepcon.enums.device_type_enum import KeepconDeviceType
from common.utils.date_util import get_now_timestamp_ms


class KeepconReg(models.Model):
    """HTTP 调用方注册（内部投递消息等 API 使用 access_key）。"""

    name = models.CharField(max_length=128)
    access_key = models.CharField(max_length=64)
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_keepcon"
        db_table = "reg"
        constraints = [
            models.UniqueConstraint(fields=["access_key"], name="keepcon_reg_access_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["name"], name="keepcon_reg_name_idx"),
            models.Index(fields=["status"], name="keepcon_reg_status_idx"),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class KeepconDevice(models.Model):
    """终端设备；WebSocket hello 使用 device_key + secret。"""

    device_key = models.CharField(max_length=64)
    secret = models.CharField(max_length=64)
    device_type = models.SmallIntegerField(default=KeepconDeviceType.MOBILE)
    name = models.CharField(max_length=128, default="")
    status = models.SmallIntegerField(default=1)
    next_seq = models.BigIntegerField(default=0)
    last_seen_at = models.PositiveBigIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_keepcon"
        db_table = "device"
        constraints = [
            models.UniqueConstraint(fields=["device_key"], name="keepcon_device_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["device_type"], name="keepcon_device_type_idx"),
            models.Index(fields=["status"], name="keepcon_device_status_idx"),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class KeepconMessage(models.Model):
    """按设备单调 seq 的下行消息；状态 pending → delivered → acked。"""

    MSG_PENDING = 0
    MSG_DELIVERED = 1
    MSG_ACKED = 2

    device = models.ForeignKey(
        KeepconDevice,
        on_delete=models.CASCADE,
        db_column="did",
        related_name="messages",
    )
    seq = models.BigIntegerField()
    payload = models.TextField(default="{}")
    status = models.SmallIntegerField(default=MSG_PENDING)
    idem_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_keepcon"
        db_table = "message"
        constraints = [
            models.UniqueConstraint(
                fields=["device", "seq"],
                name="keepcon_message_device_seq_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["device", "status", "seq"], name="keepcon_msg_dev_st_seq_idx"),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.ct = get_now_timestamp_ms()
        super().save(*args, **kwargs)
