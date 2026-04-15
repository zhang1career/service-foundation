"""Config entry CRUD with cache bump."""
from __future__ import annotations

import json

from common.utils.django_util import schedule_on_commit

from app_config.enums import ConfigEntryPublic
from app_config.repos import config_entry_repo
from app_config.services.config_cache_service import bump_config_cache_generation
from app_config.services.config_condition_validate import normalize_and_validate_condition


def _coerce_public(raw) -> int:
    v = int(raw)
    if v not in ConfigEntryPublic.values():
        raise ValueError("public must be 0 (private) or 1 (public)")
    return v


def _normalize_public_row_condition(condition_raw: str) -> str:
    """public=1: condition must be empty object {}."""
    s = (condition_raw or "").strip() or "{}"
    try:
        obj = json.loads(s)
    except json.JSONDecodeError as exc:
        raise ValueError(f"condition must be valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("condition must be a JSON object")
    if len(obj) > 0:
        raise ValueError("public entry condition must be empty object {}")
    return "{}"


class ConfigEntryService:
    @staticmethod
    def create(rid: int, config_key: str, condition: str, value: str, public: int) -> dict:
        key = (config_key or "").strip()
        if not key:
            raise ValueError("config_key is required")
        if value is None:
            raise ValueError("value is required")
        pub = _coerce_public(public)
        if pub == ConfigEntryPublic.PUBLIC:
            cond = _normalize_public_row_condition(condition)
        else:
            cond = normalize_and_validate_condition(rid, condition)
        row = config_entry_repo.create_entry(rid, key, cond, value, pub)
        schedule_on_commit(bump_config_cache_generation, rid)
        return ConfigEntryService._to_dict(row)

    @staticmethod
    def update(
        entry_id: int,
        config_key: str | None = None,
        condition: str | None = None,
        value: str | None = None,
        public: int | None = None,
    ) -> dict:
        row = config_entry_repo.get_entry_by_id(entry_id)
        if not row:
            raise ValueError("entry not found")
        rid = row.rid_id
        effective_public = _coerce_public(public) if public is not None else int(row.public)

        cond_normalized: str | None = None
        if condition is not None:
            if effective_public == ConfigEntryPublic.PUBLIC:
                cond_normalized = _normalize_public_row_condition(condition)
            else:
                cond_normalized = normalize_and_validate_condition(rid, condition)
        elif public is not None and effective_public == ConfigEntryPublic.PUBLIC:
            cond_normalized = "{}"

        pub_normalized: int | None = None
        if public is not None:
            pub_normalized = _coerce_public(public)

        updated = config_entry_repo.update_entry(
            entry_id, config_key, cond_normalized, value, pub_normalized
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
            "public": int(row.public),
            "value": row.value,
            "ct": row.ct,
            "ut": row.ut,
        }
