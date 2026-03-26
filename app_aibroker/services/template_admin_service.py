from app_aibroker.repos import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)


def _tpl_dict(t):
    return {
        "id": t.id,
        "template_key": t.template_key,
        "version": t.version,
        "constraint_type": t.constraint_type,
        "body": t.body,
        "variables_schema_json": t.variables_schema_json,
        "output_schema_json": t.output_schema_json,
        "status": t.status,
        "ct": t.ct,
        "ut": t.ut,
    }


class TemplateAdminService:
    @staticmethod
    def create_by_payload(payload: dict) -> dict:
        key = (payload.get("template_key") or "").strip()
        version = int(payload.get("version", 1))
        constraint_type = int(payload.get("constraint_type", 0))
        body = (payload.get("body") or "").strip()
        if not key or not body:
            raise ValueError("template_key and body are required")
        t = create_template(
            template_key=key,
            version=version,
            constraint_type=constraint_type,
            body=body,
            variables_schema_json=payload.get("variables_schema_json"),
            output_schema_json=payload.get("output_schema_json"),
            status=int(payload.get("status", 1)),
        )
        return _tpl_dict(t)

    @staticmethod
    def list_all(template_key: str = None) -> list:
        return [_tpl_dict(x) for x in list_templates(template_key)]

    @staticmethod
    def get_one(template_id: int) -> dict:
        t = get_template(template_id)
        if not t:
            raise ValueError("template not found")
        return _tpl_dict(t)

    @staticmethod
    def update_by_payload(template_id: int, payload: dict) -> dict:
        t = update_template(
            template_id,
            body=payload.get("body") if "body" in payload else None,
            constraint_type=int(payload["constraint_type"]) if "constraint_type" in payload else None,
            variables_schema_json=payload.get("variables_schema_json")
            if "variables_schema_json" in payload
            else None,
            output_schema_json=payload.get("output_schema_json") if "output_schema_json" in payload else None,
            status=int(payload["status"]) if "status" in payload else None,
        )
        if not t:
            raise ValueError("template not found")
        return _tpl_dict(t)

    @staticmethod
    def delete(template_id: int) -> bool:
        if not delete_template(template_id):
            raise ValueError("template not found")
        return True
