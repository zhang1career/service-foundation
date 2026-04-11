from __future__ import annotations

from typing import Optional

from app_config.models import ConfigConditionField

_DB = "config_rw"


def list_fields_for_rid(rid: int) -> list[ConfigConditionField]:
    return list(
        ConfigConditionField.objects.using(_DB).filter(rid_id=rid).order_by("field_key")
    )


def list_all_fields() -> list[ConfigConditionField]:
    return list(
        ConfigConditionField.objects.using(_DB).select_related("rid").all().order_by("-id")
    )


def get_field_by_id(field_id: int) -> Optional[ConfigConditionField]:
    return ConfigConditionField.objects.using(_DB).filter(id=field_id).first()


def create_field(rid: int, field_key: str, description: str = "") -> ConfigConditionField:
    return ConfigConditionField.objects.using(_DB).create(
        rid_id=rid,
        field_key=field_key.strip(),
        description=description.strip(),
    )


def update_field(
    field_id: int,
    field_key: str | None = None,
    description: str | None = None,
) -> Optional[ConfigConditionField]:
    row = get_field_by_id(field_id)
    if not row:
        return None
    update_fields: list[str] = []
    if field_key is not None:
        row.field_key = field_key.strip()
        update_fields.append("field_key")
    if description is not None:
        row.description = description.strip()
        update_fields.append("description")
    if update_fields:
        row.save(using=_DB, update_fields=update_fields)
    return row


def delete_field(field_id: int) -> bool:
    deleted, _ = ConfigConditionField.objects.using(_DB).filter(id=field_id).delete()
    return deleted > 0
