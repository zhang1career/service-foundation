from common.consts.string_const import STRING_EMPTY


def rec_service_start(datacenter_id: int,
                      machine_id: int,
                      brief: str = STRING_EMPTY,
                      detail_dict: dict = None) -> int:
    # lazy load
    from app_snowflake.repos.event_repo import create_event
    from app_snowflake.enums.event_type_enum import EventTypeEnum
    from app_snowflake.models.event import EventDetail

    # prepare data
    detail = EventDetail(**detail_dict)

    # query
    event = create_event(datacenter_id,
                         machine_id,
                         EventTypeEnum.SERVICE_START,
                         brief,
                         detail)

    return event.id


def rec_clock_backward(datacenter_id: int,
                       machine_id: int,
                       brief: str = STRING_EMPTY,
                       detail_dict: dict = None) -> int:
    # lazy load
    from app_snowflake.repos.event_repo import create_event
    from app_snowflake.enums.event_type_enum import EventTypeEnum
    from app_snowflake.models.event import EventDetail

    # prepare data
    detail = EventDetail(**detail_dict)

    # query
    event = create_event(datacenter_id,
                         machine_id,
                         EventTypeEnum.CLOCK_BACKWARD,
                         brief,
                         detail)

    return event.id


def rec_sequence_overflow(datacenter_id: int,
                          machine_id: int,
                          brief: str = STRING_EMPTY,
                          detail_dict: dict = None) -> int:
    # lazy load
    from app_snowflake.repos.event_repo import create_event
    from app_snowflake.enums.event_type_enum import EventTypeEnum
    from app_snowflake.models.event import EventDetail

    # prepare data
    detail = EventDetail(**detail_dict)

    # query
    event = create_event(datacenter_id,
                         machine_id,
                         EventTypeEnum.SEQUENCE_OVERFLOW,
                         brief,
                         detail)

    return event.id
