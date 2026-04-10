from collections import defaultdict

from django.conf import settings

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter
from providers.embedding_provider import SimpleTextEmbeddingProvider
from app_searchrec.adapters.index_store import _norm_term, _tokenize
from app_searchrec.models import SearchRecDocTerm


def _milvus_vector_score(item):
    if "score" in item:
        return float(item["score"])
    return float(item.get("vector_score", 0.0))


def _qdrant_doc_id(payload, item):
    raw = payload.get("id")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    raw = item.get("id")
    return str(raw).strip() if raw is not None else ""


class DbVectorAdapter:
    """Lexical overlap score from `doc_term` rows; tokenization matches `DbIndexAdapter`."""

    def reset(self):
        return

    def upsert_documents(self, rid: int, docs):
        return

    def search(self, rid: int, query, top_k):
        q_terms = {_norm_term(t) for t in _tokenize(query)}
        if not q_terms:
            return []
        rows = (
            SearchRecDocTerm.objects.filter(rid_id=int(rid), term__in=q_terms)
            .values("doc_key", "term")
            .iterator(chunk_size=2000)
        )
        by_doc: dict[str, set[str]] = defaultdict(set)
        for r in rows:
            by_doc[r["doc_key"]].add(r["term"])
        items = []
        for doc_key, doc_terms in by_doc.items():
            overlap = len(q_terms & doc_terms)
            if overlap > 0:
                items.append({"id": doc_key, "vector_score": float(overlap)})
        items.sort(key=lambda x: x["vector_score"], reverse=True)
        return items[: int(top_k)]


class MilvusVectorAdapter(BaseHttpAdapter):
    adapter_name = "milvus"

    def __init__(self):
        self._collection = str(settings.SEARCHREC_MILVUS_COLLECTION).strip()
        super().__init__(
            base_url=settings.SEARCHREC_MILVUS_ENDPOINT,
            api_key=settings.SEARCHREC_MILVUS_API_KEY,
            auth_mode="bearer",
        )

    def reset(self):
        return

    def upsert_documents(self, rid: int, docs):
        self._request(
            method="POST",
            path="/v1/vector/upsert",
            json_body={"collection": self._collection, "rid": int(rid), "documents": docs},
        )

    def search(self, rid: int, query, top_k):
        if not query or query == "*":
            return []
        response = self._request(
            method="POST",
            path="/v1/vector/search",
            json_body={
                "collection": self._collection,
                "rid": int(rid),
                "query": query,
                "top_k": int(top_k),
            },
        )
        body = response.json()
        raw_items = body.get("items") if isinstance(body, dict) else None
        items = raw_items if isinstance(raw_items, list) else []
        remote = []
        for item in items:
            raw_id = item.get("id")
            doc_id = str(raw_id).strip() if raw_id is not None else ""
            if not doc_id:
                continue
            remote.append({"id": doc_id, "vector_score": _milvus_vector_score(item)})
        return remote[:top_k]


class QdrantVectorAdapter(BaseHttpAdapter):
    adapter_name = "qdrant"

    def __init__(self):
        self._collection = str(settings.SEARCHREC_QDRANT_COLLECTION).strip()
        self._embedding = SimpleTextEmbeddingProvider()
        super().__init__(
            base_url=settings.SEARCHREC_QDRANT_URL,
            api_key=settings.SEARCHREC_QDRANT_API_KEY,
            auth_mode="api-key",
        )

    def reset(self):
        return

    def upsert_documents(self, rid: int, docs):
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
                    "payload": {"id": doc_id, "rid": int(rid)},
                }
            )
        if points:
            self._request(
                method="PUT",
                path=f"/collections/{self._collection}/points",
                json_body={"points": points},
            )

    def search(self, rid: int, query, top_k):
        if not query or query == "*":
            return []
        query_vector = self._embedding.encode(query)
        response = self._request(
            method="POST",
            path=f"/collections/{self._collection}/points/search",
            json_body={
                "vector": query_vector,
                "limit": int(top_k),
                "with_payload": True,
                "filter": {
                    "must": [{"key": "rid", "match": {"value": int(rid)}}],
                },
            },
        )
        body = response.json()
        raw_result = body.get("result") if isinstance(body, dict) else None
        items = raw_result if isinstance(raw_result, list) else []
        remote = []
        for item in items:
            payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
            pr = payload.get("rid")
            if pr is not None and int(pr) != int(rid):
                continue
            doc_id = _qdrant_doc_id(payload, item)
            if not doc_id:
                continue
            remote.append({"id": doc_id, "vector_score": float(item.get("score", 0.0))})
        return remote[:top_k]


def build_vector_adapter():
    milvus_on = settings.SEARCHREC_MILVUS_ENABLED
    qdrant_on = settings.SEARCHREC_QDRANT_ENABLED
    if milvus_on and qdrant_on:
        raise ValueError(
            "SEARCHREC_MILVUS_ENABLED and SEARCHREC_QDRANT_ENABLED cannot both be true; "
            "enable at most one remote vector backend"
        )
    if milvus_on:
        return MilvusVectorAdapter()
    if qdrant_on:
        return QdrantVectorAdapter()
    return DbVectorAdapter()
