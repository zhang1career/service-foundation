"""Condition field metadata CRUD with cache bump (per plan)."""
from __future__ import annotations

from common.utils.django_util import schedule_on_commit

from app_config.repos import condition_field_repo
from app_config.services.config_cache_service import bump_config_cache_generation


class ConfigConditionFieldService:
    @staticmethod
    def create(rid: int, field_key: str, description: str = "") -> dict:
        fk = (field_key or "").strip()
        if not fk:
            raise ValueError("field_key is required")
        row = condition_field_repo.create_field(rid, fk, description or "")
        schedule_on_commit(bump_config_cache_generation, rid)
        return ConfigConditionFieldService._to_dict(row)

    @staticmethod
    def update(field_id: int, field_key: str | None = None, description: str | None = None) -> dict:
        row = condition_field_repo.get_field_by_id(field_id)
        if not row:
            raise ValueError("field not found")
        rid = row.rid_id
        updated = condition_field_repo.update_field(field_id, field_key, description)
        if not updated:
            raise ValueError("field not found")
        schedule_on_commit(bump_config_cache_generation, rid)
        return ConfigConditionFieldService._to_dict(updated)

    @staticmethod
    def delete(field_id: int) -> bool:
        row = condition_field_repo.get_field_by_id(field_id)
        if not row:
            raise ValueError("field not found")
        rid = row.rid_id
        ok = condition_field_repo.delete_field(field_id)
        if not ok:
            raise ValueError("field not found")
        schedule_on_commit(bump_config_cache_generation, rid)
        return True

    @staticmethod
    def list_all() -> list[dict]:
        return [ConfigConditionFieldService._to_dict(x) for x in condition_field_repo.list_all_fields()]

    @staticmethod
    def _to_dict(row) -> dict:
        return {
            "id": row.id,
            "rid": row.rid_id,
            "reg_name": row.rid.name if row.rid_id else "",
            "field_key": row.field_key,
            "description": row.description,
            "ct": row.ct,
            "ut": row.ut,
        }
