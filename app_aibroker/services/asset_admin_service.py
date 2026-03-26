from app_aibroker.repos import create_asset, get_asset_by_id
from common.enums.content_type_enum import ContentTypeEnum


def _parse_content_type(raw) -> int:
    if raw is None:
        return ContentTypeEnum.APPLICATION_OCTET_STREAM.value
    try:
        v = int(raw)
        ContentTypeEnum(v)
        return v
    except (ValueError, TypeError):
        raise ValueError("invalid content_type")


class AssetAdminService:
    @staticmethod
    def create_for_reg(reg_id: int, payload: dict) -> dict:
        bucket = (payload.get("oss_bucket") or "").strip()
        key = (payload.get("oss_key") or "").strip()
        if not bucket or not key:
            raise ValueError("oss_bucket and oss_key are required")
        ct = _parse_content_type(payload.get("content_type"))
        a = create_asset(reg_id, bucket, key, content_type=ct)
        return {
            "id": a.id,
            "oss_bucket": a.oss_bucket,
            "oss_key": a.oss_key,
            "content_type": a.content_type,
            "ct": a.ct,
        }

    @staticmethod
    def get_one(asset_id: int, reg_id: int) -> dict:
        a = get_asset_by_id(asset_id)
        if not a or a.reg_id != reg_id:
            raise ValueError("asset not found")
        return {
            "id": a.id,
            "reg_id": a.reg_id,
            "oss_bucket": a.oss_bucket,
            "oss_key": a.oss_key,
            "content_type": a.content_type,
            "ct": a.ct,
        }
