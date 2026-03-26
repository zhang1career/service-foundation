from django.conf import settings

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter
from app_searchrec.adapters.embedding_provider import SimpleTextEmbeddingProvider


class MemoryVectorAdapter:
    def __init__(self):
        self._vectors = {}

    def reset(self):
        self._vectors = {}

    def upsert_documents(self, docs):
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                continue
            tags = [str(t).strip().lower() for t in (payload.get("tags") or []) if str(t).strip()]
            title = str(payload.get("title", "")).lower()
            content = str(payload.get("content", "")).lower()
            self._vectors[doc_id] = {
                "id": doc_id,
                "profile_terms": set(tags + title.split() + content.split()),
            }

    def search(self, query, top_k):
        terms = set(str(query or "").lower().split())
        if not terms:
            return []
        items = []
        for item in self._vectors.values():
            overlap = len(terms & item["profile_terms"])
            if overlap <= 0:
                continue
            items.append({"id": item["id"], "vector_score": float(overlap)})
        items.sort(key=lambda x: x["vector_score"], reverse=True)
        return items[:top_k]


class MilvusVectorAdapter(BaseHttpAdapter):
    adapter_name = "milvus"

    def __init__(self):
        self._collection = str(getattr(settings, "SEARCHREC_MILVUS_COLLECTION", "searchrec_vectors")).strip()
        super().__init__(
            base_url=getattr(settings, "SEARCHREC_MILVUS_ENDPOINT", ""),
            api_key=getattr(settings, "SEARCHREC_MILVUS_API_KEY", ""),
            auth_mode="bearer",
        )

    def reset(self):
        return

    def upsert_documents(self, docs):
        self._request(
            method="POST",
            path="/v1/vector/upsert",
            json_body={"collection": self._collection, "documents": docs},
        )

    def search(self, query, top_k):
        if not query or query == "*":
            return []
        response = self._request(
            method="POST",
            path="/v1/vector/search",
            json_body={"collection": self._collection, "query": query, "top_k": int(top_k)},
        )
        items = (response.json() or {}).get("items") or []
        remote = []
        for item in items:
            doc_id = str(item.get("id") or "")
            if not doc_id:
                continue
            remote.append({"id": doc_id, "vector_score": float(item.get("score", item.get("vector_score", 0.0)))})
        return remote[:top_k]


class QdrantVectorAdapter(BaseHttpAdapter):
    adapter_name = "qdrant"

    def __init__(self):
        self._collection = str(getattr(settings, "SEARCHREC_QDRANT_COLLECTION", "searchrec_vectors")).strip()
        self._embedding = SimpleTextEmbeddingProvider()
        super().__init__(
            base_url=getattr(settings, "SEARCHREC_QDRANT_URL", ""),
            api_key=getattr(settings, "SEARCHREC_QDRANT_API_KEY", ""),
            auth_mode="api-key",
        )

    def reset(self):
        return

    def upsert_documents(self, docs):
        points = []
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                continue
            text = f"{payload.get('title', '')} {payload.get('content', '')} {' '.join([str(t) for t in (payload.get('tags') or [])])}"
            points.append(
                {
                    "id": doc_id,
                    "vector": self._embedding.encode(text),
                    "payload": {"id": doc_id},
                }
            )
        if points:
            self._request(
                method="PUT",
                path=f"/collections/{self._collection}/points",
                json_body={"points": points},
            )

    def search(self, query, top_k):
        if not query or query == "*":
            return []
        query_vector = self._embedding.encode(query)
        response = self._request(
            method="POST",
            path=f"/collections/{self._collection}/points/search",
            json_body={"vector": query_vector, "limit": int(top_k), "with_payload": True},
        )
        items = (response.json() or {}).get("result") or []
        remote = []
        for item in items:
            payload = item.get("payload") or {}
            doc_id = str(payload.get("id") or item.get("id") or "")
            if not doc_id:
                continue
            remote.append({"id": doc_id, "vector_score": float(item.get("score", 0.0))})
        return remote[:top_k]


def build_vector_adapter(backend):
    backend = (backend or "memory").strip().lower()
    if backend == "milvus":
        return MilvusVectorAdapter()
    if backend == "qdrant":
        return QdrantVectorAdapter()
    return MemoryVectorAdapter()
