from decimal import Decimal

from django.conf import settings

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter
from app_searchrec.models import SearchRecDocument


class DbFeatureStoreAdapter:
    def reset(self):
        return

    def upsert_documents(self, rid: int, docs):
        return

    def get_doc_features(self, rid: int, doc_id):
        doc_id = str(doc_id or "").strip()
        if not doc_id:
            return {
                "score_boost": 1.0,
                "popularity_score": 0.0,
                "freshness_score": 0.0,
            }
        doc = (
            SearchRecDocument.objects.filter(rid_id=int(rid), doc_key=doc_id)
            .only("score_boost", "popularity_score", "freshness_score")
            .first()
        )
        if not doc:
            return {
                "score_boost": 1.0,
                "popularity_score": 0.0,
                "freshness_score": 0.0,
            }
        return {
            "score_boost": float(doc.score_boost),
            "popularity_score": float(doc.popularity_score or Decimal("0")),
            "freshness_score": float(doc.freshness_score or Decimal("0")),
        }

    def get_user_features(self, user_profile):
        if user_profile is None:
            user_profile = {}
        preferred = user_profile.get("preferred_tags")
        recent = user_profile.get("recent_queries")
        if not isinstance(preferred, list):
            preferred = []
        if not isinstance(recent, list):
            recent = []
        return {
            "preferred_tags": [str(t).lower() for t in preferred],
            "recent_queries": [str(q) for q in recent],
            "affinity_boost": float(user_profile.get("affinity_boost", 1.0)),
        }


class FeastFeatureStoreAdapter(BaseHttpAdapter):
    adapter_name = "feast"

    def __init__(self):
        super().__init__(
            base_url=settings.SEARCHREC_FEAST_ONLINE_URL,
            api_key=settings.SEARCHREC_FEAST_API_KEY,
            auth_mode="bearer",
        )

    def reset(self):
        return

    def upsert_documents(self, rid: int, docs):
        """Online features are read from Feast; local upsert does not push to Feast in this adapter."""

    def get_doc_features(self, rid: int, doc_id):
        if not doc_id:
            return {"score_boost": 1.0, "popularity_score": 0.0, "freshness_score": 0.0}
        raw = self._request(
            method="POST",
            path="/doc_features",
            json_body={"rid": int(rid), "doc_id": str(doc_id)},
        ).json()
        data = raw if isinstance(raw, dict) else {}
        return {
            "score_boost": float(data.get("score_boost", 1.0)),
            "popularity_score": float(data.get("popularity_score", 0.0)),
            "freshness_score": float(data.get("freshness_score", 0.0)),
        }

    def get_user_features(self, user_profile):
        profile = {} if user_profile is None else user_profile
        raw = self._request(
            method="POST", path="/user_features", json_body={"user_profile": profile}
        ).json()
        data = raw if isinstance(raw, dict) else {}
        preferred = data.get("preferred_tags")
        recent = data.get("recent_queries")
        if not isinstance(preferred, list):
            preferred = []
        if not isinstance(recent, list):
            recent = []
        return {
            "preferred_tags": [str(t).lower() for t in preferred],
            "recent_queries": [str(q) for q in recent],
            "affinity_boost": float(data.get("affinity_boost", 1.0)),
        }


def build_feature_store_adapter():
    if settings.SEARCHREC_FEAST_ENABLED:
        return FeastFeatureStoreAdapter()
    return DbFeatureStoreAdapter()
