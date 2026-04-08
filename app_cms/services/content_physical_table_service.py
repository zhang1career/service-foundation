from __future__ import annotations

import re
from typing import Any

from django.db import connections, router

from app_cms.models.content_meta import CmsContentMeta
from app_cms.schema.content_meta_fields import (
    column_allows_sql_null,
    column_index_kind,
    ddl_column_definition,
    ddl_column_definition_tail,
    index_definition_sql,
    infer_sql_default,
    reserved_row_column_sql,
)


def _columns_map_from_fields(fields: dict[str, Any] | None) -> dict[str, dict]:
    if not isinstance(fields, dict):
        return {}
    cols = fields.get("columns")
    if not isinstance(cols, list):
        return {}
    out: dict[str, dict] = {}
    for c in cols:
        if isinstance(c, dict):
            n = c.get("name")
            if isinstance(n, str) and n:
                out[n] = c
    return out


def _column_comment_signature(col: dict[str, Any]) -> str:
    raw = col.get("comment")
    if not isinstance(raw, str):
        return ""
    return raw.strip()


def _column_def_signature(col: dict[str, Any]) -> tuple[Any, ...]:
    ph = (col.get("physical") or "").strip().lower()
    return (
        ph,
        column_allows_sql_null(col),
        column_index_kind(col),
        infer_sql_default(col),
        _column_comment_signature(col),
    )


def _index_signature(idx: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    cols = idx.get("columns") or []
    return bool(idx.get("unique")), tuple(cols)


def _fetch_secondary_index_definitions(cursor, table: str) -> list[dict[str, Any]]:
    cursor.execute(
        """
        SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME != 'PRIMARY'
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """,
        [table],
    )
    rows = cursor.fetchall() or []
    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        name, non_unique, _seq, col_name = r[0], r[1], r[2], r[3]
        if name not in grouped:
            grouped[name] = {"name": name, "unique": non_unique == 0, "columns": []}
        grouped[name]["columns"].append(col_name)
    return list(grouped.values())


def _sync_secondary_indexes(cursor, table: str, desired_indexes: list[dict[str, Any]]) -> None:
    desired_sigs = {_index_signature(x) for x in desired_indexes if isinstance(x, dict)}
    current = _fetch_secondary_index_definitions(cursor, table)
    for ix in current:
        if _index_signature(ix) not in desired_sigs:
            cursor.execute(f"ALTER TABLE `{table}` DROP INDEX `{ix['name']}`")

    current2 = _fetch_secondary_index_definitions(cursor, table)
    current_sigs = {_index_signature(x) for x in current2}
    for j, idx in enumerate(desired_indexes):
        if not isinstance(idx, dict):
            continue
        sig = _index_signature(idx)
        if sig in current_sigs:
            continue
        frag = index_definition_sql(table, idx, j)
        cursor.execute(f"ALTER TABLE `{table}` ADD {frag}")
        current_sigs.add(sig)


class ContentPhysicalTableService:
    @staticmethod
    def _cms_connection():
        alias = router.db_for_write(CmsContentMeta)
        if alias is None:
            alias = "cms_rw"
        return connections[alias]

    def ensure_table(self, meta: CmsContentMeta) -> None:
        table = meta.physical_table_name()
        if not self._is_safe_identifier(table):
            raise ValueError(f"Invalid derived table name for content_meta.name={meta.name}")
        if self._table_exists(table):
            return
        self._create_table_from_schema(meta, table)

    def sync_schema(self, meta: CmsContentMeta, *, previous_fields: dict[str, Any]) -> None:
        """Diff ``previous_fields`` vs ``meta.fields`` and ALTER the row table (ADD / CHANGE / DROP + indexes)."""
        table = meta.physical_table_name()
        if not self._is_safe_identifier(table):
            raise ValueError(f"Invalid derived table name for content_meta.name={meta.name}")
        fields = meta.fields
        if not isinstance(fields, dict):
            raise ValueError("content_meta.fields must be an object")
        columns = fields.get("columns")
        if not isinstance(columns, list) or len(columns) < 1:
            raise ValueError("content_meta.fields.columns is missing or empty")

        desired_map: dict[str, dict] = {}
        for col in columns:
            if not isinstance(col, dict):
                continue
            n = col.get("name")
            if isinstance(n, str) and n:
                desired_map[n] = col
        if len(desired_map) != len(columns):
            raise ValueError("Invalid column definitions")

        if not self._table_exists(table):
            self._create_table_from_schema(meta, table)
            return

        old_map = _columns_map_from_fields(previous_fields)

        conn = self._cms_connection()
        with conn.cursor() as cursor:
            old_names = set(old_map.keys())
            new_names = set(desired_map.keys())

            for name in sorted(old_names - new_names):
                cursor.execute(f"ALTER TABLE `{table}` DROP COLUMN `{name}`")

            for name in sorted(new_names - old_names):
                cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN {ddl_column_definition(desired_map[name])}")

            for name in sorted(old_names & new_names):
                if _column_def_signature(old_map[name]) != _column_def_signature(desired_map[name]):
                    tail = ddl_column_definition_tail(desired_map[name])
                    cursor.execute(f"ALTER TABLE `{table}` CHANGE COLUMN `{name}` `{name}` {tail}")

            indexes = fields.get("indexes")
            desired_indexes = indexes if isinstance(indexes, list) else []
            _sync_secondary_indexes(cursor, table, desired_indexes)

    def drop_if_exists(self, meta: CmsContentMeta) -> None:
        table = meta.physical_table_name()
        if not self._is_safe_identifier(table):
            return
        if not self._table_exists(table):
            return
        with self._cms_connection().cursor() as cursor:
            cursor.execute(f"DROP TABLE `{table}`")

    def _create_table_from_schema(self, meta: CmsContentMeta, table: str) -> None:
        fields = meta.fields
        columns = fields.get("columns") if isinstance(fields, dict) else None
        if not isinstance(columns, list):
            raise ValueError("content_meta.fields.columns is missing")

        pieces: list[str] = ["`id` bigint unsigned NOT NULL AUTO_INCREMENT"]
        for col in columns:
            if not isinstance(col, dict):
                continue
            pieces.append(ddl_column_definition(col))
        for frag in reserved_row_column_sql():
            pieces.append(frag)

        pieces.append("PRIMARY KEY (`id`)")

        indexes = fields.get("indexes") if isinstance(fields, dict) else None
        if isinstance(indexes, list):
            for j, idx in enumerate(indexes):
                if isinstance(idx, dict):
                    pieces.append(index_definition_sql(table, idx, j))

        body = ",\n          ".join(pieces)
        sql = f"""
        CREATE TABLE `{table}` (
          {body}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        with self._cms_connection().cursor() as cursor:
            cursor.execute(sql)

    def _table_exists(self, table: str) -> bool:
        with self._cms_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s
                """,
                [table],
            )
            row = cursor.fetchone()
        return bool(row and row[0])

    @staticmethod
    def _is_safe_identifier(name: str) -> bool:
        return bool(re.match(r"^[a-z][a-z0-9_]{0,62}$", name))
