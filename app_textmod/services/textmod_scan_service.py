from __future__ import annotations

from django.conf import settings

from app_textmod.enums.suggestion_enum import TextmodSuggestionEnum
from app_textmod.services.ac_automaton import iter_ac_hits
from app_textmod.services.automaton_store import get_published_version, load_automaton_for_version
from app_textmod.services.lexicon_publish_service import LexiconPublishService
from app_textmod.services.text_normalizer import normalize_for_match


class TextmodScanService:
    @staticmethod
    def _severity_from_api(suggestion: str) -> int:
        if suggestion == "block":
            return 3
        if suggestion == "review":
            return 2
        return 1

    @classmethod
    def scan(cls, *, text: str, lexicon_id: int) -> dict:
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        max_chars = int(settings.TEXTMOD_MAX_TEXT_CHARS)
        if len(text) > max_chars:
            raise ValueError(f"text too long (max {max_chars} characters)")

        version = get_published_version(int(lexicon_id))
        if version is None:
            raise ValueError("no published lexicon version")

        auto = load_automaton_for_version(version)
        opt = LexiconPublishService.norm_options()
        norm, norm_to_orig = normalize_for_match(text, **opt)

        hits_raw: list[dict] = []
        for start, end, pid in iter_ac_hits(auto, norm):
            if pid < 0 or pid >= len(auto.words):
                continue
            o_start = norm_to_orig[start] if start < len(norm_to_orig) else 0
            o_end = norm_to_orig[end - 1] + 1 if end - 1 < len(norm_to_orig) else o_start
            hits_raw.append(
                {
                    "start_pos": int(o_start),
                    "end_pos": int(o_end),
                    "word": auto.words[pid],
                    "entry_id": int(auto.entry_ids[pid]),
                    "label_id": int(auto.label_ids[pid]),
                    "suggestion": TextmodSuggestionEnum.to_api(int(auto.suggestions[pid])),
                    "priority": int(auto.priorities[pid]),
                }
            )

        # De-dupe identical spans with identical entry_id
        seen: set[tuple[int, int, int]] = set()
        hits: list[dict] = []
        for h in sorted(hits_raw, key=lambda x: (x["start_pos"], x["end_pos"], -x["priority"])):
            key = (h["start_pos"], h["end_pos"], h["entry_id"])
            if key in seen:
                continue
            seen.add(key)
            hits.append(h)

        overall = TextmodSuggestionEnum.PASS.value
        if any(h["suggestion"] == "block" for h in hits):
            overall = TextmodSuggestionEnum.BLOCK.value
        elif any(h["suggestion"] == "review" for h in hits):
            overall = TextmodSuggestionEnum.REVIEW.value

        primary_label_id = 0
        best = 0
        for h in hits:
            sev = cls._severity_from_api(str(h["suggestion"]))
            if sev > best:
                best = sev
                primary_label_id = int(h["label_id"])

        return {
            "lexicon_id": int(lexicon_id),
            "lexicon_version_id": int(version.id),
            "lexicon_version_seq": int(version.seq),
            "normalized": norm,
            "suggestion": TextmodSuggestionEnum.to_api(int(overall)),
            "label_id": int(primary_label_id),
            "hits": hits,
        }
