from __future__ import annotations

import hashlib

from django.conf import settings

from app_textmod.enums.lexicon_version_status_enum import LexiconVersionStatusEnum
from app_textmod.models import LexiconEntry, LexiconVersion
from app_textmod.services.ac_automaton import build_ac_from_normalized_patterns, CompiledAutomaton
from app_textmod.services.automaton_store import automaton_cache_clear, resolve_blob_path
from app_textmod.services.text_normalizer import normalize_for_match
from common.utils.date_util import get_now_timestamp_ms


class LexiconPublishService:
    @staticmethod
    def norm_options() -> dict:
        return {
            "strip_edges": bool(settings.TEXTMOD_NORM_STRIP_EDGES),
            "fold_case_ascii": bool(settings.TEXTMOD_NORM_FOLD_CASE_ASCII),
            "fullwidth_to_halfwidth_ascii": bool(settings.TEXTMOD_NORM_FULLWIDTH_TO_HALFWIDTH_ASCII),
            "drop_zero_width": bool(settings.TEXTMOD_NORM_DROP_ZERO_WIDTH),
        }

    @classmethod
    def publish(cls, lexicon_id: int) -> LexiconVersion:
        opt = cls.norm_options()
        rows = list(
            LexiconEntry.objects.using("textmod_rw")
            .filter(lex_id=lexicon_id, enabled=1)
            .order_by("id")
        )

        items: list[tuple[str, int, str, int, int, int, int]] = []
        for e in rows:
            w = (e.word or "").strip()
            if not w:
                continue
            norm, _map = normalize_for_match(w, **opt)
            if not norm:
                continue
            items.append((norm, len(norm), w, int(e.id), int(e.label_id), int(e.suggestion), int(e.priority)))

        ac = build_ac_from_normalized_patterns(items)

        now_ms = get_now_timestamp_ms()
        last = (
            LexiconVersion.objects.using("textmod_rw")
            .filter(lex_id=lexicon_id)
            .order_by("-seq", "-id")
            .first()
        )
        next_seq = int(last.seq) + 1 if last else 1

        LexiconVersion.objects.using("textmod_rw").filter(
            lex_id=lexicon_id,
            status=int(LexiconVersionStatusEnum.PUBLISHED),
        ).update(status=int(LexiconVersionStatusEnum.ARCHIVED))

        rel = f"{lexicon_id}/{next_seq}.bin"
        version = LexiconVersion.objects.using("textmod_rw").create(
            lex_id=lexicon_id,
            seq=next_seq,
            status=int(LexiconVersionStatusEnum.DRAFT),
            blob_relpath=rel,
            blob_checksum="",
            entry_count=len(items),
            published_at=0,
            ct=now_ms,
        )

        out_path = resolve_blob_path(version)
        ac.dump_path(out_path)
        digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
        version.blob_checksum = digest
        version.status = int(LexiconVersionStatusEnum.PUBLISHED)
        version.published_at = now_ms
        version.save(
            using="textmod_rw",
            update_fields=["blob_checksum", "status", "published_at"],
        )
        automaton_cache_clear()
        return version


def compiled_from_entries_for_tests(rows: list[LexiconEntry]) -> CompiledAutomaton:
    """Build automaton in-process (tests) without filesystem."""
    opt = LexiconPublishService.norm_options()
    items: list[tuple[str, int, str, int, int, int, int]] = []
    for e in rows:
        w = (e.word or "").strip()
        if not w:
            continue
        norm, _m = normalize_for_match(w, **opt)
        if not norm:
            continue
        items.append((norm, len(norm), w, int(e.id), int(e.label_id), int(e.suggestion), int(e.priority)))
    return build_ac_from_normalized_patterns(items)
