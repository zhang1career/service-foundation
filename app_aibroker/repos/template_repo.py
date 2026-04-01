from typing import Optional

from common.utils.date_util import get_now_timestamp_ms

from app_aibroker.models import PromptTemplate


def create_template(
    template_key: str,
    constraint_type: int,
    body: str,
    description: str = "",
    param_specs: str = None,
    resp_specs: str = None,
    status: int = 1,
) -> PromptTemplate:
    now_ms = get_now_timestamp_ms()
    db = "aibroker_rw"
    return PromptTemplate.objects.using(db).create(
        template_key=template_key,
        constraint_type=constraint_type,
        description=description,
        body=body,
        param_specs=param_specs,
        resp_specs=resp_specs,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_templates(template_key: str = None):
    qs = PromptTemplate.objects.using("aibroker_rw").all()
    if template_key:
        qs = qs.filter(template_key=template_key)
    return list(qs.order_by("template_key"))


def get_template(template_id: int) -> Optional[PromptTemplate]:
    return PromptTemplate.objects.using("aibroker_rw").filter(id=template_id).first()


def get_template_by_key(template_key: str) -> Optional[PromptTemplate]:
    return (
        PromptTemplate.objects.using("aibroker_rw")
        .filter(template_key=template_key, status=1)
        .first()
    )


def get_latest_template(template_key: str) -> Optional[PromptTemplate]:
    return get_template_by_key(template_key)


def update_template(
    template_id: int,
    body: str = None,
    constraint_type: int = None,
    description: str = None,
    param_specs: str = None,
    resp_specs: str = None,
    status: int = None,
) -> Optional[PromptTemplate]:
    t = get_template(template_id)
    if not t:
        return None
    fields = []
    if body is not None:
        t.body = body
        fields.append("body")
    if constraint_type is not None:
        t.constraint_type = constraint_type
        fields.append("constraint_type")
    if description is not None:
        t.description = description
        fields.append("description")
    if param_specs is not None:
        t.param_specs = param_specs
        fields.append("param_specs")
    if resp_specs is not None:
        t.resp_specs = resp_specs
        fields.append("resp_specs")
    if status is not None:
        t.status = status
        fields.append("status")
    if fields:
        t.ut = get_now_timestamp_ms()
        fields.append("ut")
        t.save(using="aibroker_rw", update_fields=fields)
    return t


def delete_template(template_id: int) -> bool:
    deleted, _ = PromptTemplate.objects.using("aibroker_rw").filter(id=template_id).delete()
    return deleted > 0
