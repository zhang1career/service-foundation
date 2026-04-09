#!/usr/bin/env python3
import json
import time
from urllib import request


BASE = "http://127.0.0.1:8000/api/searchrec"


def post(path, payload):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    with request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    cost_ms = (time.perf_counter() - start) * 1000
    return data, cost_ms


def main():
    rid = 1
    docs = {
        "rid": rid,
        "documents": [
            {
                "id": "news_1",
                "title": "AI Search for E-commerce",
                "content": "Hybrid retrieval with lexical and vector search.",
                "tags": ["search", "ai", "ecommerce"],
                "score_boost": 1.0,
            },
            {
                "id": "news_2",
                "title": "Recommendation Ranking Pipeline",
                "content": "CTR and freshness based ranking strategy.",
                "tags": ["recommend", "ranking"],
                "score_boost": 1.1,
            },
        ]
    }
    upsert_resp, upsert_ms = post("/index/upsert", docs)
    print(f"upsert {upsert_ms:.2f}ms => {json.dumps(upsert_resp, ensure_ascii=False)}")

    search_resp, search_ms = post(
        "/search",
        {
            "rid": rid,
            "query": "hybrid search ranking",
            "top_k": 5,
            "preferred_tags": ["search"],
        },
    )
    print(f"search {search_ms:.2f}ms => {json.dumps(search_resp, ensure_ascii=False)}")

    rec_resp, rec_ms = post(
        "/recommend",
        {
            "rid": rid,
            "user_profile": {
                "preferred_tags": ["recommend"],
                "recent_queries": ["ctr ranking"],
            },
            "top_k": 5,
        },
    )
    print(f"recommend {rec_ms:.2f}ms => {json.dumps(rec_resp, ensure_ascii=False)}")

    rank_resp, rank_ms = post(
        "/rank",
        {
            "strategy": "hybrid",
            "candidates": [
                {"id": "news_1", "base_score": 0.72, "ctr_score": 0.35, "freshness_score": 0.42},
                {"id": "news_2", "base_score": 0.60, "ctr_score": 0.55, "freshness_score": 0.30},
            ],
        },
    )
    print(f"rank {rank_ms:.2f}ms => {json.dumps(rank_resp, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
