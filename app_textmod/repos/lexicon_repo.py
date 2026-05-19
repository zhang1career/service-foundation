from __future__ import annotations

from django.db import transaction

from app_textmod.models import Lexicon, LexiconEntry
from common.utils.date_util import get_now_timestamp_ms
from app_textmod.enums.lexicon_biz_type_enum import coerce_lexicon_biz_type_id


def create_lexicon(*, name: str, biz_type: object = None) -> Lexicon:
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required")
    bt = coerce_lexicon_biz_type_id(biz_type)
    now = get_now_timestamp_ms()
    return Lexicon.objects.using("textmod_rw").create(
        name=name,
        biz_type=bt,
        ct=now,
        ut=now,
    )


def list_lexicons() -> list[Lexicon]:
    return list(Lexicon.objects.using("textmod_rw").all().order_by("-id"))


def get_lexicon(lexicon_id: int) -> Lexicon | None:
    return Lexicon.objects.using("textmod_rw").filter(id=lexicon_id).first()


def list_entries_for_lexicon(lexicon_id: int, *, limit: int = 500) -> list[LexiconEntry]:
    lim = max(1, min(int(limit), 2000))
    return list(
        LexiconEntry.objects.using("textmod_rw")
        .filter(lex_id=lexicon_id)
        .order_by("-id")[:lim]
    )


def list_entries_for_lexicon_page(
    *,
    lexicon_id: int,
    page: int,
    page_size: int,
    word: str | None = None,
    label_id: int | None = None,
    suggestion: int | None = None,
    enabled: int | None = None,
    sort_by: str = "ct",
    sort_dir: str = "desc",
) -> tuple[int, list[LexiconEntry]]:
    qs = LexiconEntry.objects.using("textmod_rw").filter(lex_id=int(lexicon_id))
    if word:
        qs = qs.filter(word=str(word).strip())
    if label_id is not None:
        qs = qs.filter(label_id=int(label_id))
    if suggestion is not None:
        qs = qs.filter(suggestion=int(suggestion))
    if enabled is not None:
        qs = qs.filter(enabled=int(enabled))

    sort_field = "priority" if sort_by == "priority" else "ct"
    is_asc = sort_dir == "asc"
    if sort_field == "priority":
        ordering = ["priority", "id"] if is_asc else ["-priority", "-id"]
    else:
        ordering = ["ct", "id"] if is_asc else ["-ct", "-id"]
    qs = qs.order_by(*ordering)

    page_norm = max(1, int(page))
    page_size_norm = max(1, min(int(page_size), 200))
    total = qs.count()
    start = (page_norm - 1) * page_size_norm
    rows = list(qs[start : start + page_size_norm])
    return int(total), rows


def get_lexicon_entry(*, lexicon_id: int, entry_id: int) -> LexiconEntry | None:
    return (
        LexiconEntry.objects.using("textmod_rw")
        .filter(lex_id=int(lexicon_id), id=int(entry_id))
        .first()
    )


def add_entries(
    *,
    lexicon_id: int,
    entries: list[dict],
    batch_max: int,
) -> int:
    if batch_max <= 0:
        raise ValueError("invalid batch_max")
    if not entries:
        raise ValueError("entries is required")
    if len(entries) > batch_max:
        raise ValueError(f"too many entries (max {batch_max})")

    now = get_now_timestamp_ms()
    objs: list[LexiconEntry] = []
    for row in entries:
        word = str(row.get("word", "")).strip()
        if not word:
            continue
        objs.append(
            LexiconEntry(
                lex_id=int(lexicon_id),
                word=word[:512],
                label_id=int(row.get("label_id", 0)),
                suggestion=int(row.get("suggestion", 0)),
                priority=int(row.get("priority", 0)),
                enabled=1 if bool(row.get("enabled", True)) else 0,
                ct=now,
            )
        )
    if not objs:
        raise ValueError("no valid entries")

    with transaction.atomic(using="textmod_rw"):
        LexiconEntry.objects.using("textmod_rw").bulk_create(objs)
        Lexicon.objects.using("textmod_rw").filter(id=lexicon_id).update(ut=now)
    return len(objs)


def create_entry(
    *,
    lexicon_id: int,
    word: str,
    label_id: int,
    suggestion: int,
    priority: int,
    enabled: int,
) -> LexiconEntry:
    wd = (word or "").strip()
    if not wd:
        raise ValueError("word is required")
    now = get_now_timestamp_ms()
    with transaction.atomic(using="textmod_rw"):
        entry = LexiconEntry.objects.using("textmod_rw").create(
            lex_id=int(lexicon_id),
            word=wd[:512],
            label_id=int(label_id),
            suggestion=int(suggestion),
            priority=int(priority),
            enabled=1 if int(enabled) else 0,
            ct=now,
        )
        Lexicon.objects.using("textmod_rw").filter(id=int(lexicon_id)).update(ut=now)
    return entry


def update_entry(
    *,
    lexicon_id: int,
    entry_id: int,
    word: str,
    label_id: int,
    suggestion: int,
    priority: int,
    enabled: int,
) -> LexiconEntry:
    entry = get_lexicon_entry(lexicon_id=int(lexicon_id), entry_id=int(entry_id))
    if entry is None:
        raise ValueError("entry not found")
    wd = (word or "").strip()
    if not wd:
        raise ValueError("word is required")
    now = get_now_timestamp_ms()
    with transaction.atomic(using="textmod_rw"):
        entry.word = wd[:512]
        entry.label_id = int(label_id)
        entry.suggestion = int(suggestion)
        entry.priority = int(priority)
        entry.enabled = 1 if int(enabled) else 0
        entry.save(
            using="textmod_rw",
            update_fields=["word", "label_id", "suggestion", "priority", "enabled"],
        )
        Lexicon.objects.using("textmod_rw").filter(id=int(lexicon_id)).update(ut=now)
    return entry


def update_entry_enabled(*, lexicon_id: int, entry_id: int, enabled: int) -> LexiconEntry:
    entry = get_lexicon_entry(lexicon_id=int(lexicon_id), entry_id=int(entry_id))
    if entry is None:
        raise ValueError("entry not found")
    now = get_now_timestamp_ms()
    with transaction.atomic(using="textmod_rw"):
        entry.enabled = 1 if int(enabled) else 0
        entry.save(using="textmod_rw", update_fields=["enabled"])
        Lexicon.objects.using("textmod_rw").filter(id=int(lexicon_id)).update(ut=now)
    return entry


def delete_entry(*, lexicon_id: int, entry_id: int) -> bool:
    now = get_now_timestamp_ms()
    with transaction.atomic(using="textmod_rw"):
        deleted, _ = (
            LexiconEntry.objects.using("textmod_rw")
            .filter(lex_id=int(lexicon_id), id=int(entry_id))
            .delete()
        )
        if deleted:
            Lexicon.objects.using("textmod_rw").filter(id=int(lexicon_id)).update(ut=now)
            return True
    return False
