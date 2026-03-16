"""Text normalization utilities."""

import re
from typing import Optional


def _is_cjk(c: str) -> bool:
    """
    True if c is a CJK ideograph (covers 简体中文、繁体中文 and common CJK).
    Works on Unicode code points; encoding-agnostic (caller decodes bytes to str).
    """
    if not c or len(c) != 1:
        return False
    o = ord(c)
    # CJK Unified Ideographs (U+4E00–U+9FFF): 简体、繁体共用
    if 0x4E00 <= o <= 0x9FFF:
        return True
    # CJK Unified Ideographs Extension A
    if 0x3400 <= o <= 0x4DBF:
        return True
    # CJK Compatibility Ideographs, etc.
    if 0xF900 <= o <= 0xFAFF:
        return True
    return False


def _is_basic_latin_letter(c: str) -> bool:
    """True if c is a-z or A-Z (basic Latin letter, for English word boundary)."""
    if not c or len(c) != 1:
        return False
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def _decide_join(
    last_before: Optional[str], first_after: Optional[str], line_before_rstrip: str
) -> tuple[str, bool]:
    """
    Returns (separator, remove_trailing_hyphen).
    separator: '' or ' '
    remove_trailing_hyphen: whether to drop trailing hyphen from line_before (English line-break hyphen).
    """
    if last_before is None and first_after is None:
        return " ", False
    if last_before is None:
        return " ", False
    if first_after is None:
        return " ", False

    both_cjk = _is_cjk(last_before) and _is_cjk(first_after)
    if both_cjk:
        return "", False

    both_latin = _is_basic_latin_letter(last_before) and _is_basic_latin_letter(first_after)
    if both_latin:
        # English line-break hyphen: "pre-\nvious" -> remove hyphen and newline
        if line_before_rstrip.endswith("-"):
            return "", True
        return " ", False

    # One side Latin, one side other; or other language: default to space
    return " ", False


def normalize_single_paragraph(text: str) -> str:
    """
    Normalize input as single paragraph: process each newline by language context.
    - 中文(简体/繁体) adjacent to 中文: remove newline and surrounding spaces (no space).
    - Both sides English: if line ends with hyphen, remove hyphen and newline; else replace newline with space.
    - One English one other: newline -> space.
    - Other: newline -> space.
    Operates on Unicode str; encoding (UTF-8 or else) is handled by caller.
    """
    if not text or not isinstance(text, str):
        return (text or "").strip()

    # Normalize line endings to \n only
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\r", "\n", text)
    lines = re.split(r"\n", text)

    if not lines:
        return ""

    acc = lines[0].rstrip()
    for i in range(1, len(lines)):
        curr = lines[i].lstrip()
        prev_rstrip = acc.rstrip()
        last_char = prev_rstrip[-1] if prev_rstrip else None
        first_char = curr[0] if curr else None
        sep, remove_hyphen = _decide_join(last_char, first_char, prev_rstrip)

        if remove_hyphen and prev_rstrip.endswith("-"):
            acc = prev_rstrip[:-1] + sep + curr
        else:
            acc = prev_rstrip + sep + curr
    # Collapse multiple spaces and strip
    acc = re.sub(r" +", " ", acc)
    return acc.strip()
