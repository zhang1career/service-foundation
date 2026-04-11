"""Config entry CRUD with cache bump."""
from __future__ import annotations

from common.utils.django_util import schedule_on_commit

from app_config.repos import config_entry_repo
from app_config.services.config_cache_service import bump_config_cache_generation
from app_config.services.config_condition_validate import normalize_and_validate_condition


class ConfigEntryService:
    @staticmethod
    def create(rid: int, config_key: str, condition: str, value: str) -> dict:
        key = (config_key or "").strip()
        if not key:
            raise ValueError("config_key is required")
        if value is None:
            raise ValueError("value is required")
        cond = normalize_and_validate_condition(rid, condition)
        row = config_entry_repo.create_entry(rid, key, cond, value)
        schedule_on_commit(bump_config_cache_generation, rid)
        return ConfigEntryService._to_dict(row)

    @staticmethod
    def update(
        entry_id: int,
        config_key: str | None = None,
        condition: str | None = None,
        value: str | None = None,
    ) -> dict:
        row = config_entry_repo.get_entry_by_id(entry_id)
        if not row:
            raise ValueError("entry not found")
        rid = row.rid_id
        cond_normalized: str | None = None
        if condition is not None:
            cond_normalized = normalize_and_validate_condition(rid, condition)
        updated = config_entry_repo.update_entry(
            entry_id, config_key, cond_normalized, value
        )
        if not updated:
            raise ValueError("entry not found")
        schedule_on_commit(bump_config_cache_generation, rid)
        return ConfigEntryService._to_dict(updated)

    @staticmethod
    def delete(entry_id: int) -> bool:
        row = config_entry_repo.get_entry_by_id(entry_id)
        if not row:
            raise ValueError("entry not found")
        rid = row.rid_id
        ok = config_entry_repo.delete_entry(entry_id)
        if not ok:
            raise ValueError("entry not found")
        schedule_on_commit(bump_config_cache_generation, rid)
        return True

    @staticmethod
    def list_all() -> list[dict]:
        return [ConfigEntryService._to_dict(x) for x in config_entry_repo.list_all_entries()]

    @staticmethod
    def _to_dict(row) -> dict:
        return {
            "id": row.id,
            "rid": row.rid_id,
            "reg_name": row.rid.name if row.rid_id else "",
            "config_key": row.config_key,
            "condition": row.condition,
            "value": row.value,
            "ct": row.ct,
            "ut": row.ut,
        }
