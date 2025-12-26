from dataclasses import dataclass

from common.consts.string_const import STRING_EMPTY


@dataclass
class Result:
    is_ok: bool = True
    err_msg: str = STRING_EMPTY
    data: any = None
