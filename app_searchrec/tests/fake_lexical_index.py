"""In-memory lexical index for tests only (no MySQL). Mirrors DbIndexAdapter scoring semantics."""

import math
import re
import time
from collections import Counter


def _tokenize(text):
    text = text or ""
    return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())


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
