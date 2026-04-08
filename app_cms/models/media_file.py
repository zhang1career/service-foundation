from __future__ import annotations

from django.db import models

from common.utils.date_util import get_now_timestamp_ms

# Aligns with cms-agg ``media_file.status`` when transcoding finished and asset is usable.
MEDIA_FILE_STATUS_READY = 3


class CmsMediaFile(models.Model):
    """Minimal media row used by CMS content FKs (matches cms-agg media_file)."""

    original_name = models.CharField(max_length=255)
    mime_type = models.PositiveSmallIntegerField(default=0)
    size_bytes = models.PositiveBigIntegerField(default=0)
    raw_path = models.CharField(max_length=255)
    transcoded_path = models.CharField(max_length=255, null=True, blank=True)
    cdn_url = models.CharField(max_length=255, null=True, blank=True)
    status = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    ct = models.BigIntegerField()
    ut = models.BigIntegerField()

    class Meta:
        db_table = "media_file"

    def save(self, *args, **kwargs) -> None:
        now = get_now_timestamp_ms()
        if self.pk is None and self.ct is None:
            self.ct = now
        self.ut = now
        super().save(*args, **kwargs)

    def is_ready(self) -> bool:
        return self.status == MEDIA_FILE_STATUS_READY
