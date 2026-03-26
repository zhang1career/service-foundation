from typing import Optional

from app_user.repos import get_event_by_id, list_events, update_event_fields, delete_event
from common.consts.query_const import LIMIT_PAGE, LIMIT_LIST
from common.utils.page_util import build_page


def _to_dict(event) -> dict:
    return {
        "id": event.id,
        "biz_type": event.biz_type,
        "status": event.status,
        "level": event.level,
        "verify_code_id": event.verify_code_id,
        "verify_ref_id": event.verify_ref_id,
        "notice_target": event.notice_target,
        "notice_channel": event.notice_channel,
        "payload_json": event.payload_json,
        "message": event.message,
        "ct": event.ct,
        "ut": event.ut,
    }


class EventService:
    @staticmethod
    def list_events(offset: int = 0, limit: int = LIMIT_PAGE) -> dict:
        if limit <= 0:
            limit = LIMIT_PAGE
        if limit > LIMIT_LIST:
            limit = LIMIT_LIST
        rows, total = list_events(offset=offset, limit=limit)
        data = [_to_dict(item) for item in rows]
        next_offset = offset + limit if offset + limit < total else None
        return build_page(data_list=data, next_offset=next_offset, total_num=total)

    @staticmethod
    def get_event(event_id: int) -> Optional[dict]:
        row = get_event_by_id(event_id)
        return _to_dict(row) if row else None

    @staticmethod
    def update_event_by_payload(event_id: int, payload: dict) -> Optional[dict]:
        update_map = {}
        if "biz_type" in payload:
            update_map["biz_type"] = int(payload.get("biz_type"))
        if "status" in payload:
            update_map["status"] = int(payload.get("status"))
        if "level" in payload:
            update_map["level"] = int(payload.get("level"))
        if "verify_code_id" in payload:
            update_map["verify_code_id"] = int(payload.get("verify_code_id"))
        if "verify_ref_id" in payload:
            update_map["verify_ref_id"] = int(payload.get("verify_ref_id"))
        if "notice_target" in payload:
            update_map["notice_target"] = (payload.get("notice_target") or "").strip()
        if "notice_channel" in payload:
            update_map["notice_channel"] = int(payload.get("notice_channel"))
        if "payload_json" in payload:
            update_map["payload_json"] = payload.get("payload_json") or "{}"
        if "message" in payload:
            update_map["message"] = (payload.get("message") or "").strip()
        row = update_event_fields(event_id=event_id, **update_map)
        return _to_dict(row) if row else None

    @staticmethod
    def delete_event(event_id: int) -> bool:
        return delete_event(event_id=event_id)
