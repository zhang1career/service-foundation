from enum import IntEnum


class ServiceRegStatus(IntEnum):
    """Microservice `reg` caller table: `status` column (0 disabled, 1 enabled).

    Shared by app_aibroker, app_notice, app_verify, app_searchrec `reg` models.
    """

    DISABLED = 0
    ENABLED = 1

    @classmethod
    def values(cls) -> list[int]:
        return [item.value for item in cls]
