"""
字典查询接口：GET ?codes=classification,source_type
返回 { "classification": [{ "k": "Claim", "v": "claim" }, ...], ... }
"""
from common.views.dict_codes_view import DictCodesView

DictView = DictCodesView
