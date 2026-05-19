from __future__ import annotations

from enum import IntEnum


class LexiconBizTypeEnum(IntEnum):
    """词库业务场景类型（整型 id 存 lex.biz_type）。"""

    DEFAULT = 0
    GENERAL = 1
    UGC = 2
    IM = 3
    LIVE = 4
    COMMENT = 5
    PROFILE = 6
    SEARCH = 7


_LEXICON_BIZ_TYPE_ZH = {
    LexiconBizTypeEnum.DEFAULT: "默认",
    LexiconBizTypeEnum.GENERAL: "通用文本",
    LexiconBizTypeEnum.UGC: "用户生成内容",
    LexiconBizTypeEnum.IM: "即时通讯",
    LexiconBizTypeEnum.LIVE: "直播",
    LexiconBizTypeEnum.COMMENT: "评论",
    LexiconBizTypeEnum.PROFILE: "资料昵称",
    LexiconBizTypeEnum.SEARCH: "搜索词",
}


def lexicon_biz_type_label_zh(value: int) -> str:
    """Human-readable label; unknown ids are surfaced explicitly."""
    try:
        return _LEXICON_BIZ_TYPE_ZH[LexiconBizTypeEnum(int(value))]
    except (ValueError, KeyError):
        return f"未知({int(value)})"


def coerce_lexicon_biz_type_id(raw: object, *, field_name: str = "biz_type") -> int:
    """
    Normalize API/input to a defined ``LexiconBizTypeEnum`` value.

    Accepts int or str digits; ``None`` / missing / empty string → ``DEFAULT``.
    """
    if raw is None or raw == "":
        return int(LexiconBizTypeEnum.DEFAULT)
    if isinstance(raw, bool):
        raise ValueError(f"{field_name} must be an integer enum id")
    if isinstance(raw, int):
        v = raw
    else:
        s = str(raw).strip()
        if not s:
            return int(LexiconBizTypeEnum.DEFAULT)
        try:
            v = int(s)
        except ValueError as e:
            raise ValueError(f"{field_name} must be an integer enum id") from e
    try:
        LexiconBizTypeEnum(v)
    except ValueError:
        raise ValueError(f"{field_name} is not a valid LexiconBizTypeEnum id: {v}") from None
    return int(v)


def lexicon_biz_type_choices_for_template() -> list[dict[str, int | str]]:
    """For console &lt;select&gt;: value + label."""
    return [
        {"value": int(e), "label": f"{int(e)} — {_LEXICON_BIZ_TYPE_ZH[e]}"}
        for e in LexiconBizTypeEnum
    ]
