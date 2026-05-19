import app_textmod.enums.label_enum  # noqa: F401
import app_textmod.enums.lexicon_biz_type_enum  # noqa: F401
import app_textmod.enums.suggestion_enum  # noqa: F401
import app_textmod.enums.lexicon_version_status_enum  # noqa: F401

from common.dict_catalog import register_dict_code
from app_textmod.enums.label_enum import TextmodLabelEnum
from app_textmod.enums.lexicon_biz_type_enum import LexiconBizTypeEnum, lexicon_biz_type_label_zh
from app_textmod.enums.suggestion_enum import TextmodSuggestionEnum


@register_dict_code("textmod_lexicon_biz_type")
class TextmodLexiconBizTypeDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [
            {"k": lexicon_biz_type_label_zh(int(e.value)), "v": str(int(e.value))}
            for e in LexiconBizTypeEnum
        ]


@register_dict_code("textmod_suggestion")
class TextmodSuggestionDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        return [
            {"k": "pass", "v": str(TextmodSuggestionEnum.PASS.value)},
            {"k": "review", "v": str(TextmodSuggestionEnum.REVIEW.value)},
            {"k": "block", "v": str(TextmodSuggestionEnum.BLOCK.value)},
        ]


@register_dict_code("textmod_label")
class TextmodLabelDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        out: list[dict] = []
        for e in TextmodLabelEnum:
            out.append({"k": e.name.lower(), "v": str(int(e.value))})
        return out
