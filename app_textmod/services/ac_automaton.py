from __future__ import annotations

import pickle
import struct
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app_textmod.constants import TEXTMOD_AUTOMATON_FILE_MAGIC, TEXTMOD_AUTOMATON_FORMAT_V1


@dataclass(frozen=True)
class CompiledAutomaton:
    """
    In-memory Aho–Corasick automaton + pattern metadata.

    Transition keys are Unicode code points (same representation as Python str iteration).
    """

    goto: list[dict[int, int]]
    fail: list[int]
    out: list[list[int]]
    pattern_lens: list[int]
    words: list[str]
    entry_ids: list[int]
    label_ids: list[int]
    suggestions: list[int]
    priorities: list[int]

    def dump_path(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        payload = pickle.dumps(self, protocol=4)
        with open(tmp, "wb") as f:
            f.write(TEXTMOD_AUTOMATON_FILE_MAGIC)
            f.write(struct.pack(">H", TEXTMOD_AUTOMATON_FORMAT_V1))
            f.write(payload)
        tmp.replace(path)

    @classmethod
    def load_path(cls, path: Path) -> "CompiledAutomaton":
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != TEXTMOD_AUTOMATON_FILE_MAGIC:
                raise ValueError("invalid textmod automaton magic")
            ver = struct.unpack(">H", f.read(2))[0]
            if ver != TEXTMOD_AUTOMATON_FORMAT_V1:
                raise ValueError(f"unsupported textmod automaton format: {ver}")
            obj = pickle.load(f)
        if not isinstance(obj, CompiledAutomaton):
            raise ValueError("invalid automaton payload")
        return obj


def build_ac_from_normalized_patterns(
    items: Iterable[tuple[str, int, str, int, int, int, int]],
) -> CompiledAutomaton:
    """
    Build automaton from normalized patterns.

    Each item:
      (norm_pattern, pattern_len, original_word, entry_id, label_id, suggestion, priority)
    """
    norm_patterns: list[str] = []
    pattern_lens: list[int] = []
    words: list[str] = []
    entry_ids: list[int] = []
    label_ids: list[int] = []
    suggestions: list[int] = []
    priorities: list[int] = []

    for norm, plen, ow, eid, lid, sug, pri in items:
        if not norm:
            continue
        pid = len(norm_patterns)
        norm_patterns.append(norm)
        pattern_lens.append(plen)
        words.append(ow)
        entry_ids.append(int(eid))
        label_ids.append(int(lid))
        suggestions.append(int(sug))
        priorities.append(int(pri))

    if not norm_patterns:
        return CompiledAutomaton(
            goto=[{}],
            fail=[0],
            out=[[]],
            pattern_lens=[],
            words=[],
            entry_ids=[],
            label_ids=[],
            suggestions=[],
            priorities=[],
        )

    goto: list[dict[int, int]] = [{}]
    out: list[list[int]] = [[]]
    fail: list[int] = [0]

    def new_state() -> int:
        goto.append({})
        out.append([])
        fail.append(0)
        return len(goto) - 1

    for pid, pat in enumerate(norm_patterns):
        state = 0
        for ch in pat:
            code = ord(ch)
            nxt = goto[state].get(code)
            if nxt is None:
                nxt = new_state()
                goto[state][code] = nxt
            state = nxt
        out[state].append(pid)

    q: deque[int] = deque()
    for code, nxt in goto[0].items():
        _ = code
        fail[nxt] = 0
        q.append(nxt)

    while q:
        state = q.popleft()
        for code, nxt in goto[state].items():
            f = fail[state]
            while f != 0 and code not in goto[f]:
                f = fail[f]
            fail[nxt] = goto[f][code] if code in goto[f] else 0
            merged = list(out[nxt])
            for pid in out[fail[nxt]]:
                if pid not in merged:
                    merged.append(pid)
            out[nxt] = merged
            q.append(nxt)

    return CompiledAutomaton(
        goto=goto,
        fail=fail,
        out=out,
        pattern_lens=pattern_lens,
        words=words,
        entry_ids=entry_ids,
        label_ids=label_ids,
        suggestions=suggestions,
        priorities=priorities,
    )


def iter_ac_hits(automaton: CompiledAutomaton, norm_text: str):
    """Yield (start, end_exclusive, pid) in normalized index space."""
    state = 0
    for i, ch in enumerate(norm_text):
        code = ord(ch)
        while state != 0 and code not in automaton.goto[state]:
            state = automaton.fail[state]
        if code in automaton.goto[state]:
            state = automaton.goto[state][code]
        else:
            state = 0
        for pid in automaton.out[state]:
            plen = automaton.pattern_lens[pid]
            start = i - plen + 1
            end = i + 1
            yield start, end, pid
