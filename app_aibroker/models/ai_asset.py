from django.db import models

from common.enums.content_type_enum import ContentTypeEnum


class AiAsset(models.Model):
    id = models.BigAutoField(primary_key=True)
    reg_id = models.PositiveBigIntegerField()
    oss_bucket = models.CharField(max_length=128)
    oss_key = models.CharField(max_length=512)
    content_type = models.IntegerField(default=ContentTypeEnum.APPLICATION_OCTET_STREAM.value)
    ct = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "ai_asset"
        indexes = [
            models.Index(fields=["reg_id"], name="idx_ai_asset_reg"),
        ]
