"""
Invalidation model - CloudFront-compatible cache invalidation
"""
import json

from django.db import models

from app_cdn.enums.invalidation_status_enum import InvalidationStatusEnum
from common.utils.date_util import get_now_timestamp_ms


class Invalidation(models.Model):
    """
    Cache invalidation batch (CloudFront-compatible).
    Uses id (PK) as external identifier. status: InvalidationStatusEnum id.
    """

    did = models.ForeignKey(
        "app_cdn.Distribution",
        on_delete=models.CASCADE,
        related_name="invalidations",
        db_index=True,
        db_column="did",
    )
    # Caller reference (unique per request)
    caller_reference = models.CharField(max_length=128)
    # Paths JSON: ["/path1", "/path2"]
    paths = models.TextField(default="[]")
    # Status: InvalidationStatusEnum id (0=InProgress, 1=Completed)
    status = models.SmallIntegerField(
        default=InvalidationStatusEnum.COMPLETED,
        db_index=True,
    )
    # Timestamps (milliseconds)
    ct = models.BigIntegerField(default=0)

    class Meta:
        db_table = "invalid"
        app_label = "app_cdn"

    def __str__(self):
        dist_id = self.did_id if self.did_id else "?"
        return f"{self.id} ({dist_id})" if self.pk else f"({dist_id})"

    def save(self, *args, **kwargs):
        now = get_now_timestamp_ms()
        if self.ct == 0:
            self.ct = now
        super().save(*args, **kwargs)

    def get_paths_list(self) -> list:
        """Parse paths JSON to list."""
        try:
            return json.loads(self.paths) if self.paths else []
        except (json.JSONDecodeError, TypeError):
            return []
