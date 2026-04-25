from django.db import models

from app_tcc.enums import BranchStatus, CancelReason, GlobalTxStatus
from common.enums.service_reg_status_enum import ServiceRegStatus
from common.utils.date_util import get_now_timestamp_ms


class TccParticipant(models.Model):
    access_key = models.CharField(max_length=128, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, default="")
    status = models.SmallIntegerField(
        choices=[(item.value, item.name) for item in ServiceRegStatus],
        default=ServiceRegStatus.ENABLED.value,
    )
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "reg"

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class TccBizMeta(models.Model):
    participant = models.ForeignKey(
        TccParticipant,
        on_delete=models.CASCADE,
        related_name="businesses",
        db_column="rid",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "biz_meta"
        ordering = ["id"]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class TccBranchMeta(models.Model):
    biz = models.ForeignKey(
        TccBizMeta,
        on_delete=models.CASCADE,
        related_name="branch_defs",
        db_column="biz_id",
    )
    branch_index = models.PositiveIntegerField()
    code = models.CharField(max_length=64, default="")
    name = models.CharField(max_length=255, blank=True, default="")
    try_url = models.CharField(max_length=2048)
    confirm_url = models.CharField(max_length=2048)
    cancel_url = models.CharField(max_length=2048)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "branch_meta"
        ordering = ["branch_index", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["biz", "branch_index"],
                name="tcc_branch_meta_unique_biz_branch_index",
            ),
        ]

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class TccGlobalTransaction(models.Model):
    status = models.PositiveSmallIntegerField(default=GlobalTxStatus.INIT, db_index=True)
    phase_started_at = models.BigIntegerField()
    phase_deadline_at = models.BigIntegerField(null=True, blank=True)
    await_confirm_deadline_at = models.BigIntegerField(null=True, blank=True)
    next_retry_at = models.BigIntegerField()
    retry_count = models.PositiveIntegerField(default=0)
    auto_confirm = models.BooleanField(default=True)
    manual_reason = models.TextField(blank=True, default="")
    context = models.TextField(default="{}", blank=True)
    idem_key = models.BigIntegerField(unique=True)
    last_cancel_reason = models.PositiveSmallIntegerField(default=CancelReason.UNPAID)
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "tx"
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["status", "await_confirm_deadline_at"]),
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


class TccManualReview(models.Model):
    global_tx = models.OneToOneField(
        TccGlobalTransaction,
        on_delete=models.CASCADE,
        related_name="manual_review",
        db_column="tid",
    )
    snapshot = models.TextField(default="{}")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "tx_manual_review"

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self._state.adding:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)


class TccBranch(models.Model):
    global_tx = models.ForeignKey(
        TccGlobalTransaction,
        on_delete=models.CASCADE,
        related_name="branches",
        db_column="tid",
    )
    branch_meta = models.ForeignKey(
        TccBranchMeta,
        on_delete=models.PROTECT,
        related_name="branch_runs",
        db_column="branch_meta_id",
    )
    branch_index = models.PositiveIntegerField()
    status = models.PositiveSmallIntegerField(default=BranchStatus.PENDING_TRY)
    idem_key = models.BigIntegerField()
    payload = models.TextField(default="{}", blank=True)
    last_http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    participant_last_response = models.TextField(blank=True, default="")
    ct = models.PositiveBigIntegerField(default=0)
    ut = models.PositiveBigIntegerField(default=0)

    class Meta:
        app_label = "app_tcc"
        db_table = "tx_branch"
        ordering = ["branch_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["global_tx", "branch_index"],
                name="tcc_tx_branch_unique_gtx_branch_index",
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
