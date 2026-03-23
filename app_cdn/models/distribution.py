"""
Distribution model - CloudFront-compatible CDN distribution
"""
import json
import time
import uuid

from django.db import models

from app_cdn.enums.distribution_status_enum import DistributionStatusEnum


class Distribution(models.Model):
    """
    CDN distribution (CloudFront-compatible).

    Stores distribution metadata. Origin config stored as JSON.
    Uses id (PK) as external identifier. status: DistributionStatusEnum id.
    """

    # ARN-style identifier
    arn = models.CharField(max_length=256, blank=True, default="")
    # Status: DistributionStatusEnum id (0=InProgress, 1=Deployed)
    status = models.SmallIntegerField(
        default=DistributionStatusEnum.DEPLOYED,
        db_index=True,
    )
    # Domain name for distribution (e.g. d1234.cloudfront.net -> local: cdn.example.com)
    domain_name = models.CharField(max_length=256)
    # Origin config JSON: {"Origins": {"Items": [...], "Quantity": N}, "DefaultCacheBehavior": {...}, ...}
    origin_config = models.TextField(default="{}")
    # Aliases (CNAMEs) JSON: ["cdn.example.com"]
    aliases = models.TextField(default="[]")
    # Enabled
    enabled = models.BooleanField(default=False)
    # Comment
    comment = models.CharField(max_length=256, blank=True, default="")
    # ETag for conditional updates
    etag = models.CharField(max_length=64, blank=True, default="")
    # Timestamps (milliseconds)
    ct = models.BigIntegerField(default=0)
    ut = models.BigIntegerField(default=0)

    class Meta:
        db_table = "d"
        app_label = "app_cdn"

    def __str__(self):
        return f"{self.id} ({self.domain_name})" if self.pk else f"({self.domain_name})"

    def save(self, *args, **kwargs):
        now = int(time.time() * 1000)
        if self.ct == 0:
            self.ct = now
        self.ut = now
        if not self.etag:
            self.etag = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def get_origin_config(self) -> dict:
        """Parse origin_config JSON."""
        try:
            return json.loads(self.origin_config) if self.origin_config else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_aliases_list(self) -> list:
        """Parse aliases JSON to list."""
        try:
            return json.loads(self.aliases) if self.aliases else []
        except (json.JSONDecodeError, TypeError):
            return []
