import logging
from django.db import transaction

from app_snowflake.consts.snowflake_const import MASK_RECOUNT

logger = logging.getLogger(__name__)


def get_recounter(
        datacenter_id: int,
        machine_id: int,
) -> int:
    # lazy load
    from app_snowflake.repos.recounter_repo import get_recounter

    # query
    recounter = get_recounter(datacenter_id, machine_id)

    return recounter.rc if recounter else None


@transaction.atomic
def create_or_update_recount(
        datacenter_id: int,
        machine_id: int,
) -> int:
    # lazy load
    from app_snowflake.repos.recounter_repo import create_recounter, update_recounter, get_recounter

    # fetch recounter record
    recounter = get_recounter(datacenter_id, machine_id)
    # record not exists, create new one
    if not recounter:
        create_recounter(
            datacenter_id=datacenter_id,
            machine_id=machine_id,
        )
        return 0

    # record exists, update counter
    new_count = (recounter.rc + 1) & MASK_RECOUNT  # wrap around by bit masking
    update_recounter(
        origin=recounter,
        data_dict={
            "recount": new_count
        }
    )
    # transaction will auto-commit on success
    return new_count
