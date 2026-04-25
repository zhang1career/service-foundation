from __future__ import annotations

from django.db import models

from app_saga.enums import (
    SagaInstanceStatus,
    SagaStepActionStatus,
    SagaStepCompensateStatus,
)
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.date_util import get_now_timestamp_ms


class SagaParticipant(models.Model):
    access_key = models.CharField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.SmallIntegerField(
        choices=[(item.value, item.name) for item in ServiceRegStatus],
        default=ServiceRegStatus.ENABLED.value,
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        managed = False
        app_label = "app_saga"
        db_table = "reg"

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class SagaFlow(models.Model):
    participant = models.ForeignKey(
        SagaParticipant,
        on_delete=models.CASCADE,
        related_name="flows",
        db_column="rid",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.SmallIntegerField(
        choices=[(item.value, item.name) for item in ServiceRegStatus],
        default=ServiceRegStatus.ENABLED.value,
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        managed = False
        app_label = "app_saga"
        db_table = "flow"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class SagaFlowStep(models.Model):
    flow = models.ForeignKey(
        SagaFlow,
        on_delete=models.CASCADE,
        related_name="steps",
        db_column="fid",
    )
    step_index = models.PositiveIntegerField()
    step_code = models.CharField(max_length=64, default="")
    name = models.CharField(max_length=255, blank=True, default="")
    action_url = models.CharField(max_length=2048)
    compensate_url = models.CharField(max_length=2048)
    timeout_sec = models.PositiveIntegerField(default=30)
    max_retries = models.PositiveIntegerField(default=10)
    is_need_confirm = models.SmallIntegerField(default=0)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        managed = False
        app_label = "app_saga"
        db_table = "flow_step"
        ordering = ["step_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["flow", "step_index"],
                name="flow_step_fid_step_uq",
            ),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class SagaInstance(models.Model):
    flow = models.ForeignKey(
        SagaFlow,
        on_delete=models.CASCADE,
        related_name="instances",
        db_column="fid",
    )
    participant = models.ForeignKey(
        SagaParticipant,
        on_delete=models.CASCADE,
        related_name="saga_instances",
        db_column="rid",
    )
    status = models.PositiveSmallIntegerField(default=SagaInstanceStatus.PENDING, db_index=True)
    idem_key = models.BigIntegerField(unique=True)
    context = models.TextField(default="{}")
    step_payloads = models.TextField(default="{}")
    start_body = models.TextField(default="{}")
    need_confirm = models.TextField(null=True, blank=True)
    current_step_index = models.IntegerField(default=0)
    next_retry_at = models.BigIntegerField()
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        managed = False
        app_label = "app_saga"
        db_table = "instance"
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        uf = kwargs.get("update_fields")
        if uf is not None:
            merged = {f for f in uf if f not in ("created_at", "updated_at")}
            merged.add("ut")
            if self._state.adding:
                merged.add("ct")
            kwargs["update_fields"] = list(merged)
        super().save(*args, **kwargs)


class SagaStepRun(models.Model):
    instance = models.ForeignKey(
        SagaInstance,
        on_delete=models.CASCADE,
        related_name="step_runs",
        db_column="ins_id",
    )
    flow_step = models.ForeignKey(
        SagaFlowStep,
        on_delete=models.CASCADE,
        related_name="step_runs",
        db_column="fsid",
    )
    step_index = models.PositiveIntegerField()
    action_status = models.PositiveSmallIntegerField(default=SagaStepActionStatus.PENDING)
    compensate_status = models.PositiveSmallIntegerField(default=SagaStepCompensateStatus.PENDING)
    last_http_status_action = models.PositiveSmallIntegerField(null=True, blank=True)
    last_http_status_compensate = models.PositiveSmallIntegerField(null=True, blank=True)
    last_error_action = models.TextField(blank=True, default="")
    last_error_compensate = models.TextField(blank=True, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        managed = False
        app_label = "app_saga"
        db_table = "step_run"
        ordering = ["step_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["instance", "step_index"],
                name="step_run_ins_step_uq",
            ),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        uf = kwargs.get("update_fields")
        if uf is not None:
            merged = {f for f in uf if f not in ("created_at", "updated_at")}
            merged.add("ut")
            if self._state.adding:
                merged.add("ct")
            kwargs["update_fields"] = list(merged)
        super().save(*args, **kwargs)
