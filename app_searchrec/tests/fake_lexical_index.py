"""In-memory adapters for tests only (no MySQL). Mirrors DbIndexAdapter / DbVectorAdapter semantics."""

import math
import re
import time
from collections import Counter


def _tokenize(text):
    text = text or ""
    return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())


def _norm_term(token: str) -> str:
    if len(token) <= 191:
        return token
    return token[:191]


class FakeLexicalIndexAdapter:
    def __init__(self):
        self._docs = {}

    def reset(self):
        self._docs = {}

    def upsert_documents(self, rid: int, docs):
        written = 0
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                raise ValueError("field `id` is required")
            tags = payload.get("tags") or []
            if not isinstance(tags, list):
                raise ValueError("field `tags` must be list")
            title = str(payload.get("title", "")).strip()
            content = str(payload.get("content", "")).strip()
            score_boost = float(payload.get("score_boost", 1.0))
            tokens = _tokenize(" ".join([title, content, " ".join([str(t) for t in tags])]))
            tf = Counter(tokens)
            norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0
            key = (int(rid), doc_id)
            self._docs[key] = {
                "id": doc_id,
                "rid": int(rid),
                "title": title,
                "content": content,
                "tags": [str(t).strip().lower() for t in tags if str(t).strip()],
                "score_boost": score_boost,
                "tf": tf,
                "norm": norm,
                "updated_at": int(time.time()),
            }
            written += 1
        return {"upserted": written, "total": len(self._docs)}

    def search(self, rid: int, query, top_k):
        query_tokens = _tokenize(query)
        q_tf = Counter(query_tokens)
        q_norm = math.sqrt(sum(v * v for v in q_tf.values())) or 1.0

        items = []
        for key, doc in self._docs.items():
            if key[0] != int(rid):
                continue
            dot = 0
            for token, count in q_tf.items():
                dot += count * doc["tf"].get(token, 0)
            lexical = 0.0 if not query_tokens else dot / (q_norm * doc["norm"])
            if lexical <= 0:
                continue
            items.append(
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "tags": doc["tags"],
                    "lexical_score": lexical,
                    "score_boost": doc["score_boost"],
                }
            )
        items.sort(key=lambda x: x["lexical_score"], reverse=True)
        return items[:top_k]

    def get_document(self, rid: int, doc_id):
        doc_id = str(doc_id or "").strip()
        if not doc_id:
            return None
        doc = self._docs.get((int(rid), doc_id))
        if not doc:
            return None
        return {
            "id": doc["id"],
            "title": doc["title"],
            "tags": doc["tags"],
            "score_boost": doc["score_boost"],
        }


class FakeVectorAdapter:
    """Same overlap scoring as `DbVectorAdapter` (token set ∩ query terms), in-memory."""

    def __init__(self):
        self._by_doc: dict[tuple[int, str], set[str]] = {}

    def reset(self):
        self._by_doc = {}

    def upsert_documents(self, rid: int, docs):
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                continue
            tags = payload.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            title = str(payload.get("title", "")).strip()
            content = str(payload.get("content", "")).strip()
            raw_text = " ".join([title, content, " ".join([str(t) for t in tags])])
            terms = {_norm_term(t) for t in _tokenize(raw_text)}
            self._by_doc[(int(rid), doc_id)] = terms

    def search(self, rid: int, query, top_k):
        q_terms = {_norm_term(t) for t in _tokenize(query)}
        if not q_terms:
            return []
        items = []
        for (r, doc_id), doc_terms in self._by_doc.items():
            if r != int(rid):
                continue
            overlap = len(q_terms & doc_terms)
            if overlap > 0:
                items.append({"id": doc_id, "vector_score": float(overlap)})
        items.sort(key=lambda x: x["vector_score"], reverse=True)
        return items[: int(top_k)]


class FakeFeatureStoreAdapter:
    def __init__(self):
        self._doc_features: dict[tuple[int, str], dict] = {}

    def reset(self):
        self._doc_features = {}

    def upsert_documents(self, rid: int, docs):
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                continue
            key = (int(rid), doc_id)
            self._doc_features[key] = {
                "score_boost": float(payload.get("score_boost", 1.0)),
                "popularity_score": float(payload.get("popularity_score", 0.0)),
                "freshness_score": float(payload.get("freshness_score", 0.0)),
            }

    def get_doc_features(self, rid: int, doc_id):
        doc_id = str(doc_id or "").strip()
        key = (int(rid), doc_id)
        return self._doc_features.get(
            key,
            {"score_boost": 1.0, "popularity_score": 0.0, "freshness_score": 0.0},
        )

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
