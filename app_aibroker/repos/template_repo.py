import time
from typing import Optional

from app_aibroker.models import PromptTemplate


def _now_ms() -> int:
    return int(time.time() * 1000)


def create_template(
    template_key: str,
    version: int,
    constraint_type: int,
    body: str,
    variables_schema_json: str = None,
    output_schema_json: str = None,
    status: int = 1,
) -> PromptTemplate:
    now_ms = _now_ms()
    return PromptTemplate.objects.using("aibroker_rw").create(
        template_key=template_key,
        version=version,
        constraint_type=constraint_type,
        body=body,
        variables_schema_json=variables_schema_json,
        output_schema_json=output_schema_json,
        status=status,
        ct=now_ms,
        ut=now_ms,
    )


def list_templates(template_key: str = None):
    qs = PromptTemplate.objects.using("aibroker_rw").all()
    if template_key:
        qs = qs.filter(template_key=template_key)
    return list(qs.order_by("-id"))


def get_template(template_id: int) -> Optional[PromptTemplate]:
    return PromptTemplate.objects.using("aibroker_rw").filter(id=template_id).first()


def get_template_by_key_version(template_key: str, version: int) -> Optional[PromptTemplate]:
    return (
        PromptTemplate.objects.using("aibroker_rw")
        .filter(template_key=template_key, version=version)
        .first()
    )


def get_latest_template(template_key: str) -> Optional[PromptTemplate]:
    return (
        PromptTemplate.objects.using("aibroker_rw")
        .filter(template_key=template_key, status=1)
        .order_by("-version")
        .first()
    )


def update_template(
    template_id: int,
    body: str = None,
    constraint_type: int = None,
    variables_schema_json: str = None,
    output_schema_json: str = None,
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
    if variables_schema_json is not None:
        t.variables_schema_json = variables_schema_json
        fields.append("variables_schema_json")
    if output_schema_json is not None:
        t.output_schema_json = output_schema_json
        fields.append("output_schema_json")
    if status is not None:
        t.status = status
        fields.append("status")
    if fields:
        t.ut = _now_ms()
        fields.append("ut")
        t.save(using="aibroker_rw", update_fields=fields)
    return t


def delete_template(template_id: int) -> bool:
    deleted, _ = PromptTemplate.objects.using("aibroker_rw").filter(id=template_id).delete()
    return deleted > 0
