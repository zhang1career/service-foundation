import math
import json
import re
import time
from collections import Counter

from django.conf import settings

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter


def _tokenize(text):
    text = text or ""
    return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())


def _search_response_hits(data):
    if not isinstance(data, dict):
        return []
    hits_outer = data.get("hits")
    if not isinstance(hits_outer, dict):
        return []
    inner = hits_outer.get("hits")
    return inner if isinstance(inner, list) else []


class MemoryIndexAdapter:
    def __init__(self):
        self._docs = {}

    def reset(self):
        self._docs = {}

    def upsert_documents(self, docs):
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
            self._docs[doc_id] = {
                "id": doc_id,
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

    def search(self, query, top_k):
        query_tokens = _tokenize(query)
        q_tf = Counter(query_tokens)
        q_norm = math.sqrt(sum(v * v for v in q_tf.values())) or 1.0

        items = []
        for doc in self._docs.values():
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


class OpenSearchIndexAdapter(BaseHttpAdapter):
    adapter_name = "opensearch"

    def __init__(self):
        self._index_name = str(getattr(settings, "SEARCHREC_OPENSEARCH_INDEX", "searchrec_docs")).strip()
        super().__init__(
            base_url=getattr(settings, "SEARCHREC_OPENSEARCH_URL", ""),
            api_key=getattr(settings, "SEARCHREC_OPENSEARCH_API_KEY", ""),
            auth_mode="opensearch",
        )

    def reset(self):
        return

    def upsert_documents(self, docs):
        written = 0
        lines = []
        for payload in docs:
            doc_id = str(payload.get("id", "")).strip()
            if not doc_id:
                raise ValueError("field `id` is required")
            lines.append({"index": {"_index": self._index_name, "_id": doc_id}})
            lines.append(
                {
                    "id": doc_id,
                    "title": str(payload.get("title", "")),
                    "content": str(payload.get("content", "")),
                    "tags": payload.get("tags") or [],
                    "score_boost": float(payload.get("score_boost", 1.0)),
                }
            )
            written += 1

        bulk_payload = "\n".join([json.dumps(line, ensure_ascii=False) for line in lines]) + "\n"
        self._request(method="POST", path="/_bulk", data=bulk_payload.encode("utf-8"))
        return {"upserted": written, "total": written}

    def search(self, query, top_k):
        if not query or query == "*":
            return []
        response = self._request(
            method="POST",
            path=f"/{self._index_name}/_search",
            json_body={
                "size": int(top_k),
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "content", "tags^2"],
                    }
                },
            },
        )
        data = response.json()
        hits = _search_response_hits(data)
        remote_items = []
        for hit in hits:
            src = hit.get("_source") or {}
            doc_id = str(src.get("id") or hit.get("_id") or "")
            if not doc_id:
                continue
            remote_items.append(
                {
                    "id": doc_id,
                    "title": str(src.get("title") or ""),
                    "tags": src.get("tags") or [],
                    "lexical_score": float(hit.get("_score") or 0.0),
                    "score_boost": float(src.get("score_boost", 1.0)),
                }
            )
        return remote_items[:top_k]


def build_index_adapter(backend):
    backend = (backend or "memory").strip().lower()
    if backend in ("opensearch", "elasticsearch"):
        return OpenSearchIndexAdapter()
    return MemoryIndexAdapter()
