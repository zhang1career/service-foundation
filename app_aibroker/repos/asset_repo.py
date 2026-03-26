import time
from typing import Optional

from app_aibroker.models import AiAsset
from common.enums.content_type_enum import ContentTypeEnum


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_asset(
    reg_id: int,
    oss_bucket: str,
    oss_key: str,
    *,
    content_type: int = ContentTypeEnum.APPLICATION_OCTET_STREAM.value,
) -> AiAsset:
    return AiAsset.objects.using("aibroker_rw").create(
        reg_id=reg_id,
        oss_bucket=oss_bucket,
        oss_key=oss_key,
        content_type=content_type,
        ct=_now_ms(),
    )


def get_asset_by_id(asset_id: int) -> Optional[AiAsset]:
    return AiAsset.objects.using("aibroker_rw").filter(id=asset_id).first()
