from __future__ import annotations

# Zero-width and format characters commonly used to evade filters.
_ZERO_WIDTH = frozenset(
    (
        "\u200b",
        "\u200c",
        "\u200d",
        "\ufeff",
        "\u2060",
    )
)


def _fullwidth_to_halfwidth_ascii(ch: str) -> str:
    o = ord(ch)
    if 0xFF01 <= o <= 0xFF5E:
        return chr(o - 0xFEE0)
    if o == 0x3000:
        return " "
    return ch


def normalize_for_match(
    text: str,
    *,
    strip_edges: bool = True,
    fold_case_ascii: bool = True,
    fullwidth_to_halfwidth_ascii: bool = True,
    drop_zero_width: bool = True,
) -> tuple[str, list[int]]:
    """
    Normalize text for matching and return parallel mapping norm_index → original char index.

    Each output character maps to exactly one source index in the original ``text`` (by
    Python str indexing, i.e. Unicode code points for typical CJK text).
    """
    if text is None:
        raise ValueError("text is required")

    s = text
    base = 0
    if strip_edges:
        # Strip without losing index mapping: operate on slice bounds.
        n = len(s)
        start = 0
        while start < n and s[start].isspace():
            start += 1
        end = n
        while end > start and s[end - 1].isspace():
            end -= 1
        s = s[start:end]
        base = start

    out_chars: list[str] = []
    norm_to_orig: list[int] = []

    for idx, ch in enumerate(s):
        if drop_zero_width and ch in _ZERO_WIDTH:
            continue
        if fullwidth_to_halfwidth_ascii:
            ch = _fullwidth_to_halfwidth_ascii(ch)
        if fold_case_ascii:
            o = ord(ch)
            if o <= 127:
                ch = ch.lower()
        out_chars.append(ch)
        norm_to_orig.append(base + idx)

    return "".join(out_chars), norm_to_orig
