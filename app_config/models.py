from django.db import models

from app_config.enums import ConfigEntryPublic
from common.utils.date_util import get_now_timestamp_ms


class ConfigReg(models.Model):
    """Caller registration table sf_config.reg."""

    name = models.CharField(max_length=128)
    access_key = models.CharField(max_length=64)
    status = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_config"
        db_table = "reg"
        constraints = [
            models.UniqueConstraint(fields=["access_key"], name="config_reg_access_key_uniq"),
        ]
        indexes = [
            models.Index(fields=["name"], name="config_reg_name_idx"),
            models.Index(fields=["status"], name="config_reg_status_idx"),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class ConfigConditionField(models.Model):
    """Per-caller condition field metadata (documentation / console only)."""

    rid = models.ForeignKey(
        ConfigReg,
        on_delete=models.CASCADE,
        db_column="rid",
        related_name="condition_fields",
    )
    field_key = models.CharField(max_length=128)
    description = models.CharField(max_length=512, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_config"
        db_table = "condition_meta"
        constraints = [
            models.UniqueConstraint(
                fields=["rid", "field_key"],
                name="config_cond_field_rid_key_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["rid"], name="config_cond_field_rid_idx"),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class ConfigEntry(models.Model):
    """Key-value config row with JSON condition and JSON value string."""

    rid = models.ForeignKey(
        ConfigReg,
        on_delete=models.CASCADE,
        db_column="rid",
        related_name="config_entries",
    )
    config_key = models.CharField(max_length=191)
    condition = models.TextField(default="")
    public = models.SmallIntegerField(default=ConfigEntryPublic.PRIVATE)
    value = models.TextField()
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_config"
        db_table = "config_entry"
        indexes = [
            models.Index(fields=["rid", "config_key"], name="config_entry_rid_key_idx"),
            models.Index(fields=["rid", "ut"], name="config_entry_rid_ut_idx"),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)
