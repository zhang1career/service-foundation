from django.conf import settings

from app_searchrec.adapters import (
    build_feature_store_adapter,
    build_index_adapter,
    build_vector_adapter,
)


def _clamp_top_k(requested, configured_default):
    """Resolve API `top_k` with a single defaulting step, then bound to [1, 100]."""
    if requested is None:
        effective = int(configured_default)
    else:
        try:
            effective = int(requested)
        except (TypeError, ValueError):
            effective = int(configured_default)
    if effective <= 0:
        effective = int(configured_default)
    return max(1, min(effective, 100))


def _score_boost_for_item(doc_features, item):
    """Prefer feature-store `score_boost`; otherwise item payload; default 1.0."""
    raw = doc_features.get("score_boost")
    if raw is not None:
        return float(raw)
    return float(item.get("score_boost", 1.0))


class SearchRecService:
    _index_adapter = None
    _vector_adapter = None
    _feature_store_adapter = None

    @staticmethod
    def _search_candidate_budget(top_k):
        m = int(settings.SEARCHREC_SEARCH_CANDIDATE_MULTIPLIER)
        m = max(1, min(m, 20))
        return max(1, int(top_k) * m)

    @classmethod
    def _ensure_adapters(cls):
        if cls._index_adapter is None:
            cls._index_adapter = build_index_adapter()
        if cls._vector_adapter is None:
            cls._vector_adapter = build_vector_adapter()
        if cls._feature_store_adapter is None:
            cls._feature_store_adapter = build_feature_store_adapter()

    @classmethod
    def reset(cls):
        cls._index_adapter = None
        cls._vector_adapter = None
        cls._feature_store_adapter = None

    @classmethod
    def upsert_documents(cls, docs):
        cls._ensure_adapters()
        if not isinstance(docs, list) or not docs:
            raise ValueError("field `documents` must be a non-empty list")
        index_result = cls._index_adapter.upsert_documents(docs)
        cls._vector_adapter.upsert_documents(docs)
        cls._feature_store_adapter.upsert_documents(docs)
        return index_result

    @classmethod
    def search(cls, query, top_k=10, preferred_tags=None):
        cls._ensure_adapters()
        default_top_k = int(settings.SEARCHREC_DEFAULT_TOP_K)
        top_k = _clamp_top_k(top_k, default_top_k)
        preferred_tags = [str(t).lower() for t in (preferred_tags or [])]

        budget = cls._search_candidate_budget(top_k)
        lexical_items = cls._index_adapter.search(query=query, top_k=budget)
        vector_items = cls._vector_adapter.search(query=query, top_k=budget)
        vector_score_by_id = {item["id"]: item["vector_score"] for item in vector_items}

        merge_vector = settings.SEARCHREC_MERGE_VECTOR_CANDIDATES
        if merge_vector:
            seen = {item["id"] for item in lexical_items}
            candidate_rows = list(lexical_items)
            for v in vector_items:
                doc_id = v["id"]
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                meta = cls._index_adapter.get_document(doc_id)
                if not meta:
                    continue
                candidate_rows.append(
                    {
                        "id": meta["id"],
                        "title": meta["title"],
                        "tags": meta["tags"],
                        "lexical_score": 0.0,
                        "score_boost": meta["score_boost"],
                    }
                )
        else:
            candidate_rows = list(lexical_items)

        items = []
        for item in candidate_rows:
            doc_features = cls._feature_store_adapter.get_doc_features(item["id"])
            item_tags = item.get("tags")
            if not isinstance(item_tags, list):
                item_tags = []
            overlap_tags = len(set(preferred_tags) & set(item_tags)) if preferred_tags else 0
            tag_score = 0.1 * overlap_tags
            lexical_score = float(item.get("lexical_score", 0.0))
            vector_score = float(vector_score_by_id.get(item["id"], 0.0))
            vector_blend = min(1.0, vector_score / 5.0)
            popularity = float(doc_features.get("popularity_score", 0.0))
            score_boost = _score_boost_for_item(doc_features, item)
            final_score = (0.65 * lexical_score + 0.2 * vector_blend + tag_score + 0.05 * popularity) * score_boost
            if final_score <= 0:
                continue
            items.append(
                {
                    "id": item["id"],
                    "title": item.get("title", ""),
                    "tags": item.get("tags", []),
                    "score": round(final_score, 6),
                    "features": {
                        "lexical_score": round(lexical_score, 6),
                        "vector_score": round(vector_score, 6),
                        "tag_score": round(tag_score, 6),
                        "popularity_score": round(popularity, 6),
                        "score_boost": score_boost,
                    },
                }
            )
        items.sort(key=lambda x: x["score"], reverse=True)
        return {"items": items[:top_k], "total_hits": len(items)}

    @classmethod
    def recommend(cls, user_profile, top_k=10):
        cls._ensure_adapters()
        user_features = cls._feature_store_adapter.get_user_features(user_profile)
        preferred_tags = user_features["preferred_tags"]
        recent_queries = user_features["recent_queries"]
        query = " ".join([str(q) for q in recent_queries if str(q).strip()]).strip()
        if not query:
            query = " ".join(preferred_tags)
        if not query:
            query = "*"
        result = cls.search(query=query, top_k=top_k, preferred_tags=preferred_tags)
        affinity_boost = float(user_features.get("affinity_boost", 1.0))
        for item in result["items"]:
            item["score"] = round(item["score"] * affinity_boost, 6)
            item["features"]["affinity_boost"] = affinity_boost
        result["items"].sort(key=lambda x: x["score"], reverse=True)
        return result

    @classmethod
    def rank(cls, candidates, strategy="hybrid"):
        if not isinstance(candidates, list):
            raise ValueError("field `candidates` must be list")

        ranked = []
        for item in candidates:
            base = float(item.get("base_score", 0))
            ctr = float(item.get("ctr_score", 0))
            freshness = float(item.get("freshness_score", 0))

            if strategy == "ctr_first":
                final = 0.2 * base + 0.7 * ctr + 0.1 * freshness
            elif strategy == "fresh_first":
                final = 0.2 * base + 0.2 * ctr + 0.6 * freshness
            else:
                final = 0.5 * base + 0.3 * ctr + 0.2 * freshness

            payload = dict(item)
            payload["final_score"] = round(final, 6)
            ranked.append(payload)

        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        return {"items": ranked, "count": len(ranked), "strategy": strategy}
