from typing import Optional

from app_snowflake.models.reg import SnowflakeReg


def get_reg_by_access_key_and_status(access_key: str, status: int) -> Optional[SnowflakeReg]:
    return (
        SnowflakeReg.objects.using("snowflake_rw")
        .filter(access_key=access_key, status=status)
        .first()
    )
