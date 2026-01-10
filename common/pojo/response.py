from dataclasses import dataclass, field

from common.consts.string_const import EMPTY_STRING


class ResponseEmbeddedError:
    path: str = EMPTY_STRING
    message: str = EMPTY_STRING
    rejectValue: any = None
    source: str = EMPTY_STRING


@dataclass
class Response:
    errorCode: int = 0
    data: any = None
    message: str = EMPTY_STRING
    _embedded: list[ResponseEmbeddedError] = field(default_factory=list)

    # getters
    def get_data(self):
        return self.data

    def get_message(self):
        return self.message

    def get_error_code(self):
        return self.errorCode

    def get_embedded(self):
        return self._embedded

    # checkers
    def is_success(self) -> bool:
        return self.errorCode == 0