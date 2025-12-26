import logging

from app_snowflake.enums.event_type_enum import EventTypeEnum
from app_snowflake.models.event import Event, EventDetail
from common.consts.string_const import STRING_EMPTY
from common.utils.date_util import get_now_timestamp_ms
from common.utils.json_util import json_encode

logger = logging.getLogger(__name__)


def list_event(datacenter_id: int,
               machine_id: int,
               limit: int = 1000) -> list[Event]:
    try:
        return Event.objects.using('snowflake_rw').filter(
            dcid=datacenter_id,
            mid=machine_id,
        ).order_by('-ct')[:limit]
    except Event.DoesNotExist:
        return None


def create_event(datacenter_id: int,
                 machine_id: int,
                 event_type_enum: EventTypeEnum,
                 brief: str = STRING_EMPTY,
                 detail: EventDetail = None) -> Event:
    now = get_now_timestamp_ms()
    # prepare data
    new_model_dict = {
        "dcid": datacenter_id,
        "mid": machine_id,
        "event_type": event_type_enum.value,
        "brief": brief,
        "detail": json_encode(detail.to_dict()) if detail else "",
        "ct": now,
    }
    # query
    new_model = Event.objects.using('snowflake_rw').create(**new_model_dict)

    return new_model
