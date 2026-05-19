from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django.conf import settings

from app_textmod.enums.lexicon_version_status_enum import LexiconVersionStatusEnum
from app_textmod.models import LexiconVersion
from app_textmod.services.ac_automaton import CompiledAutomaton


def _root_dir() -> Path:
    return Path(settings.TEXTMOD_AUTOMATON_DIR).resolve()


def resolve_blob_path(version: LexiconVersion) -> Path:
    rel = (version.blob_relpath or "").strip()
    if not rel or ".." in rel.split("/"):
        raise ValueError("invalid blob path")
    return _root_dir() / rel


@lru_cache(maxsize=16)
def _load_automaton_cached(blob_abs: str, checksum: str) -> CompiledAutomaton:
    _ = checksum  # checksum participates in cache key only
    return CompiledAutomaton.load_path(Path(blob_abs))


def load_automaton_for_version(version: LexiconVersion) -> CompiledAutomaton:
    path = resolve_blob_path(version)
    digest = (version.blob_checksum or "").strip()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return _load_automaton_cached(str(path), digest)


def get_published_version(lexicon_id: int) -> LexiconVersion | None:
    return (
        LexiconVersion.objects.using("textmod_rw")
        .filter(lex_id=lexicon_id, status=int(LexiconVersionStatusEnum.PUBLISHED))
        .order_by("-seq", "-id")
        .first()
    )


def automaton_cache_clear() -> None:
    _load_automaton_cached.cache_clear()
