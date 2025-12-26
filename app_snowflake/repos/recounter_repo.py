import logging

from app_snowflake.consts.recounter_const import DEFAULT_RECOUNTER
from app_snowflake.models.recounter import Recounter
from common.utils.date_util import get_now_timestamp_ms

logger = logging.getLogger(__name__)


def create_recounter(datacenter_id: int, machine_id: int) -> Recounter:
    now = get_now_timestamp_ms()
    # prepare data
    new_model_dict = {
        "dcid": datacenter_id,
        "mid": machine_id,
        "rc": DEFAULT_RECOUNTER,
        "ct": now,
        "ut": now,
    }
    # query
    new_model = Recounter.objects.using('snowflake_rw').create(**new_model_dict)

    return new_model


def update_recounter(origin: Recounter, data_dict: dict) -> int:
    now = get_now_timestamp_ms()
    # prepare data
    new_model_dict = {
        "id": origin.id,
        "dcid": origin.dcid,
        "mid": origin.mid,
        "rc": data_dict.get("recount", origin.rc),
        "ct": origin.ct,
        "ut": now,
    }
    # query
    rows = Recounter.objects.using('snowflake_rw').filter(id=origin.id).update(**new_model_dict)

    return rows


def get_recounter(datacenter_id: int, machine_id: int) -> Recounter:
    try:
        return Recounter.objects.using('snowflake_rw').get(
            dcid=datacenter_id,
            mid=machine_id,
        )
    except Recounter.DoesNotExist:
        return None
