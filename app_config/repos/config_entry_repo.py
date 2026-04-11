from __future__ import annotations

from typing import Optional

from app_config.models import ConfigEntry

_DB = "config_rw"


def list_entries_for_rid_and_key(rid: int, config_key: str) -> list[ConfigEntry]:
    return list(
        ConfigEntry.objects.using(_DB)
        .filter(rid_id=rid, config_key=config_key)
        .order_by("ut", "id")
    )


def list_all_entries() -> list[ConfigEntry]:
    return list(
        ConfigEntry.objects.using(_DB).select_related("rid").all().order_by("-id")
    )


def get_entry_by_id(entry_id: int) -> Optional[ConfigEntry]:
    return ConfigEntry.objects.using(_DB).filter(id=entry_id).first()


def create_entry(rid: int, config_key: str, condition: str, value: str) -> ConfigEntry:
    return ConfigEntry.objects.using(_DB).create(
        rid_id=rid,
        config_key=config_key.strip(),
        condition=condition,
        value=value,
    )


def update_entry(
    entry_id: int,
    config_key: str | None = None,
    condition: str | None = None,
    value: str | None = None,
) -> Optional[ConfigEntry]:
    entry = get_entry_by_id(entry_id)
    if not entry:
        return None
    update_fields: list[str] = []
    if config_key is not None:
        entry.config_key = config_key.strip()
        update_fields.append("config_key")
    if condition is not None:
        entry.condition = condition
        update_fields.append("condition")
    if value is not None:
        entry.value = value
        update_fields.append("value")
    if update_fields:
        entry.save(using=_DB, update_fields=update_fields)
    return entry


def delete_entry(entry_id: int) -> bool:
    deleted, _ = ConfigEntry.objects.using(_DB).filter(id=entry_id).delete()
    return deleted > 0
