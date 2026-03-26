from app_aibroker.repos import (
    create_provider,
    delete_provider,
    get_provider_by_id,
    list_providers,
    update_provider,
)


def _prov_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "base_url": p.base_url,
        "status": p.status,
        "ct": p.ct,
        "ut": p.ut,
    }


class ProviderService:
    @staticmethod
    def create_by_payload(payload: dict) -> dict:
        name = (payload.get("name") or "").strip()
        base_url = (payload.get("base_url") or "").strip()
        api_key = (payload.get("api_key") or "").strip()
        status = int(payload.get("status", 1))
        if not name or not base_url or not api_key:
            raise ValueError("name, base_url, api_key are required")
        p = create_provider(name, base_url, api_key, status=status)
        return _prov_dict(p)

    @staticmethod
    def list_all() -> list:
        return [_prov_dict(x) for x in list_providers()]

    @staticmethod
    def get_one(provider_id: int) -> dict:
        p = get_provider_by_id(provider_id)
        if not p:
            raise ValueError("provider not found")
        return _prov_dict(p)

    @staticmethod
    def update_by_payload(provider_id: int, payload: dict) -> dict:
        name = payload.get("name") if "name" in payload else None
        base_url = payload.get("base_url") if "base_url" in payload else None
        api_key = payload.get("api_key") if "api_key" in payload else None
        status = int(payload["status"]) if "status" in payload else None
        if base_url is not None:
            base_url = base_url.strip()
        p = update_provider(provider_id, name=name, base_url=base_url, api_key=api_key, status=status)
        if not p:
            raise ValueError("provider not found")
        return _prov_dict(p)

    @staticmethod
    def delete(provider_id: int) -> bool:
        if not delete_provider(provider_id):
            raise ValueError("provider not found")
        return True


class ModelService:
    @staticmethod
    def create_by_payload(payload: dict) -> dict:
        provider_id = int(payload.get("provider_id", 0))
        model_name = (payload.get("model_name") or "").strip()
        capability = int(payload.get("capability", 0))
        status = int(payload.get("status", 1))
        if provider_id <= 0 or not model_name:
            raise ValueError("provider_id and model_name are required")
        from app_aibroker.repos import create_model

        m = create_model(provider_id, model_name, capability=capability, status=status)
        return ModelService._to_dict(m)

    @staticmethod
    def _to_dict(m):
        return {
            "id": m.id,
            "provider_id": m.provider_id,
            "model_name": m.model_name,
            "capability": m.capability,
            "status": m.status,
            "ct": m.ct,
            "ut": m.ut,
        }

    @staticmethod
    def list_for_provider(provider_id: int) -> list:
        from app_aibroker.repos import list_models_for_provider

        return [ModelService._to_dict(x) for x in list_models_for_provider(provider_id)]

    @staticmethod
    def update(model_id: int, payload: dict) -> dict:
        from app_aibroker.repos import get_model_by_id, update_model

        m0 = get_model_by_id(model_id)
        if not m0:
            raise ValueError("model not found")
        model_name = payload.get("model_name") if "model_name" in payload else None
        capability = int(payload["capability"]) if "capability" in payload else None
        status = int(payload["status"]) if "status" in payload else None
        m = update_model(model_id, model_name=model_name, capability=capability, status=status)
        return ModelService._to_dict(m)

    @staticmethod
    def delete(model_id: int) -> bool:
        from app_aibroker.repos import delete_model

        if not delete_model(model_id):
            raise ValueError("model not found")
        return True
