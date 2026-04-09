import math
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from urllib.parse import quote

from django.conf import settings
from django.db import transaction

from app_searchrec.adapters.base_http_adapter import BaseHttpAdapter
from app_searchrec.models import SearchRecDocument, SearchRecDocTerm
from app_searchrec.tags_csv import join_tags_csv, parse_tags_csv


_TERM_MAX_LEN = 191


def _norm_term(token: str) -> str:
    if len(token) <= _TERM_MAX_LEN:
        return token
    return token[:_TERM_MAX_LEN]


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


def _hit_doc_id(src, hit):
    raw = src.get("id")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    raw = hit.get("_id")
    return str(raw).strip() if raw is not None else ""


class DbIndexAdapter:
    """Lexical index in MySQL: `doc` row + `doc_term` inverted rows; query via term union."""

    def reset(self):
        SearchRecDocTerm.objects.all().delete()
        SearchRecDocument.objects.all().delete()

    def upsert_documents(self, docs):
        written = 0
        for payload in docs:
            doc_key = str(payload.get("id", "")).strip()
            if not doc_key:
                raise ValueError("field `id` is required")
            if len(doc_key) > _TERM_MAX_LEN:
                raise ValueError(f"field `id` exceeds max length {_TERM_MAX_LEN}")
            tags = payload.get("tags") or []
            if not isinstance(tags, list):
                raise ValueError("field `tags` must be list")
            title = str(payload.get("title", "")).strip()
            content = str(payload.get("content", "")).strip()
            score_boost = float(payload.get("score_boost", 1.0))
            raw_text = " ".join([title, content, " ".join([str(t) for t in tags])])
            tokens = [_norm_term(t) for t in _tokenize(raw_text)]
            tf = Counter(tokens)
            norm_sq = sum(c * c for c in tf.values())

            with transaction.atomic():
                SearchRecDocTerm.objects.filter(doc_key=doc_key).delete()
                SearchRecDocument.objects.update_or_create(
                    doc_key=doc_key,
                    defaults={
                        "title": title[:512],
                        "content": content,
                        "tags": join_tags_csv([str(t) for t in tags]),
                        "score_boost": Decimal(str(score_boost)),
                        "lexical_norm_sq": norm_sq,
                    },
                )
                if tf:
                    SearchRecDocTerm.objects.bulk_create(
                        [
                            SearchRecDocTerm(doc_key=doc_key, term=t, tf=c)
                            for t, c in tf.items()
                        ],
                        batch_size=500,
                    )
            written += 1
        return {"upserted": written, "total": SearchRecDocument.objects.count()}

    def search(self, query, top_k):
        if not query or query == "*":
            return []
        query_tokens = _tokenize(query)
        q_tf = Counter(_norm_term(t) for t in query_tokens)
        q_norm = math.sqrt(sum(v * v for v in q_tf.values())) or 1.0

        terms = list(q_tf.keys())
        if not terms:
            return []

        rows = (
            SearchRecDocTerm.objects.filter(term__in=terms)
            .values("doc_key", "term", "tf")
            .iterator(chunk_size=2000)
        )
        by_doc: dict[str, dict[str, int]] = defaultdict(dict)
        for r in rows:
            by_doc[r["doc_key"]][r["term"]] = r["tf"]

        doc_keys = list(by_doc.keys())
        if not doc_keys:
            return []

        meta = {
            d.doc_key: d
            for d in SearchRecDocument.objects.filter(doc_key__in=doc_keys).only(
                "doc_key", "title", "tags", "score_boost", "lexical_norm_sq"
            )
        }

        items = []
        for doc_key, term_tf in by_doc.items():
            doc = meta.get(doc_key)
            if not doc:
                continue
            dot = 0.0
            for q_t, q_c in q_tf.items():
                dot += q_c * float(term_tf.get(q_t, 0))
            doc_norm_sq = int(doc.lexical_norm_sq or 0)
            doc_norm = math.sqrt(max(doc_norm_sq, 0)) or 1.0
            lexical = dot / (q_norm * doc_norm)
            if lexical <= 0:
                continue
            items.append(
                {
                    "id": doc_key,
                    "title": doc.title or "",
                    "tags": parse_tags_csv(doc.tags or ""),
                    "lexical_score": lexical,
                    "score_boost": float(doc.score_boost),
                }
            )
        items.sort(key=lambda x: x["lexical_score"], reverse=True)
        return items[:top_k]

    def get_document(self, doc_id):
        doc_id = str(doc_id or "").strip()
        if not doc_id:
            return None
        doc = SearchRecDocument.objects.filter(doc_key=doc_id).only(
            "doc_key", "title", "tags", "score_boost"
        ).first()
        if not doc:
            return None
        return {
            "id": doc.doc_key,
            "title": doc.title or "",
            "tags": parse_tags_csv(doc.tags or ""),
            "score_boost": float(doc.score_boost),
        }


class OpenSearchIndexAdapter(BaseHttpAdapter):
    adapter_name = "opensearch"

    def __init__(self):
        self._index_name = str(settings.SEARCHREC_OPENSEARCH_INDEX).strip()
        super().__init__(
            base_url=settings.SEARCHREC_OPENSEARCH_URL,
            api_key=settings.SEARCHREC_OPENSEARCH_API_KEY,
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
            src = hit.get("_source") if isinstance(hit.get("_source"), dict) else {}
            doc_id = _hit_doc_id(src, hit)
            if not doc_id:
                continue
            hit_tags = src.get("tags")
            if not isinstance(hit_tags, list):
                hit_tags = []
            raw_score = hit.get("_score")
            remote_items.append(
                {
                    "id": doc_id,
                    "title": str(src.get("title") or ""),
                    "tags": hit_tags,
                    "lexical_score": float(raw_score if raw_score is not None else 0.0),
                    "score_boost": float(src.get("score_boost", 1.0)),
                }
            )
        return remote_items[:top_k]

    def get_document(self, doc_id):
        doc_id = str(doc_id or "").strip()
        if not doc_id:
            return None
        safe_id = quote(doc_id, safe="")
        response = self._request_raw(method="GET", path=f"/{self._index_name}/_doc/{safe_id}")
        if response.status_code == 404:
            return None
        if response.status_code >= 300:
            raise RuntimeError(f"{self.adapter_name} status={response.status_code}, body={response.text}")
        data = response.json()
        src = data.get("_source") if isinstance(data.get("_source"), dict) else {}
        raw_id = src.get("id")
        resolved_id = str(raw_id).strip() if raw_id is not None else doc_id
        tags = src.get("tags")
        if not isinstance(tags, list):
            tags = []
        return {
            "id": resolved_id,
            "title": str(src.get("title") or ""),
            "tags": tags,
            "score_boost": float(src.get("score_boost", 1.0)),
        }


def build_index_adapter():
    if settings.SEARCHREC_OPENSEARCH_ENABLED:
        return OpenSearchIndexAdapter()
    return DbIndexAdapter()
