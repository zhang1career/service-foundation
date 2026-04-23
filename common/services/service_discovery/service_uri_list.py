"""Comma-separated service instance lists (Paganini ServiceUriList-compatible)."""

from __future__ import annotations

import random


def parse_comma_separated(raw: str) -> list[str]:
    parts = raw.split(",")
    out: list[str] = []
    for part in parts:
        t = part.strip()
        if t:
            out.append(t)
    return out


def pick_index(n_items: int, index: int) -> int:
    if n_items <= 0:
        return 0
    return (index % n_items + n_items) % n_items


def pick_instance(hosts: list[str], index: int | None) -> str:
    n = len(hosts)
    if n == 0:
        raise ValueError("empty service instance list")
    if index is None:
        return random.choice(hosts)
    return hosts[pick_index(n, index)]
