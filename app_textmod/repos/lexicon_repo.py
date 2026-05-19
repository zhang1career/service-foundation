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
