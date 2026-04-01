from __future__ import annotations


def unique_positive_int_ids(values, cap: int) -> list[int]:
    """Deduplicate, coerce to int, keep order, cap length; skip non-integers and non-positive."""
    uniq: list[int] = []
    seen: set[int] = set()
    for x in values:
        try:
            v = int(x)
        except (TypeError, ValueError):
            continue
        if v <= 0 or v in seen:
            continue
        seen.add(v)
        uniq.append(v)
        if len(uniq) >= cap:
            break
    return uniq
