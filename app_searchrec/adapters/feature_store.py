from django.conf import settings

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter


class MemoryFeatureStoreAdapter:
    def __init__(self):
        self._doc_features = {}

    def reset(self):
        self._doc_features = {}

    def upsert_documents(self, docs):
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                continue
            self._doc_features[doc_id] = {
                "score_boost": float(payload.get("score_boost", 1.0)),
                "popularity_score": float(payload.get("popularity_score", 0.0)),
                "freshness_score": float(payload.get("freshness_score", 0.0)),
            }

    def get_doc_features(self, doc_id):
        return self._doc_features.get(
            doc_id,
            {"score_boost": 1.0, "popularity_score": 0.0, "freshness_score": 0.0},
        )

    def get_user_features(self, user_profile):
        user_profile = user_profile or {}
        return {
            "preferred_tags": [str(t).lower() for t in (user_profile.get("preferred_tags") or [])],
            "recent_queries": [str(q) for q in (user_profile.get("recent_queries") or [])],
            "affinity_boost": float(user_profile.get("affinity_boost", 1.0)),
        }


class FeastFeatureStoreAdapter(BaseHttpAdapter):
    adapter_name = "feast"

    def __init__(self):
        super().__init__(
            base_url=getattr(settings, "SEARCHREC_FEAST_ONLINE_URL", ""),
            api_key=getattr(settings, "SEARCHREC_FEAST_API_KEY", ""),
            auth_mode="bearer",
        )

    def reset(self):
        return

    def get_doc_features(self, doc_id):
        if not doc_id:
            return {"score_boost": 1.0, "popularity_score": 0.0, "freshness_score": 0.0}
        data = self._request(method="POST", path="/doc_features", json_body={"doc_id": str(doc_id)}).json() or {}
        return {
            "score_boost": float(data.get("score_boost", 1.0)),
            "popularity_score": float(data.get("popularity_score", 0.0)),
            "freshness_score": float(data.get("freshness_score", 0.0)),
        }

    def get_user_features(self, user_profile):
        data = self._request(method="POST", path="/user_features", json_body={"user_profile": user_profile or {}}).json() or {}
        return {
            "preferred_tags": [str(t).lower() for t in (data.get("preferred_tags") or [])],
            "recent_queries": [str(q) for q in (data.get("recent_queries") or [])],
            "affinity_boost": float(data.get("affinity_boost", 1.0)),
        }


def build_feature_store_adapter(backend):
    backend = (backend or "memory").strip().lower()
    if backend == "feast":
        return FeastFeatureStoreAdapter()
    return MemoryFeatureStoreAdapter()
