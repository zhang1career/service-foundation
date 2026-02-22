# Report: Multi-application support and skills-scoped queries (app_know)

**Generated.** This document was auto-generated to report what was created or changed for multi-application support and skills-scoped queries in `app_know` (Round 4 of 4).

---

## Summary

- **Multi-application support:** `app_id` (or scope) is accepted in config/request across summary, query, and relationship APIs. All scoped data (summaries in Atlas, relationships in Neo4j) are keyed by `app_id`; knowledge CRUD remains global in MySQL.
- **Skills-scoped queries:** The logical query API supports `app_id=skills` (or any app id). Skills-scoped queries reuse the same Atlas summary relevance and Neo4j logic pipeline; no separate code path—only the `app_id` parameter.
- **Consolidation under app_know:** Existing knowledge CRUD and the new relationship, summary, and query APIs are all under `app_know` and mounted at `api/know/`.

---

## What was created or changed

### 1. API endpoints (all under `api/know/`)

| Method | Path | app_id / scope | Purpose |
|--------|------|----------------|---------|
| GET | `api/know/knowledge` | — | List knowledge |
| POST | `api/know/knowledge` | — | Create knowledge |
| GET | `api/know/knowledge/<id>` | — | Get knowledge by id |
| PUT | `api/know/knowledge/<id>` | — | Update knowledge |
| GET | `api/know/knowledge/<id>/summary` | Query `app_id` | Get summary for one knowledge item |
| POST | `api/know/knowledge/<id>/summary` | Body `app_id` required | Generate and save summary |
| GET | `api/know/knowledge/summaries` | Query `app_id`, knowledge_id, limit, offset | List summaries (app-scoped) |
| GET | `api/know/knowledge/query` | Query `query`/`q`, `app_id`, `limit` | Logical query (Atlas + Neo4j); skills when `app_id` e.g. `"skills"` |
| POST | `api/know/knowledge/query` | Body `query`/`q`, `app_id`, `limit` | Logical query (Atlas + Neo4j); skills-scoped when `app_id` set |
| GET | `api/know/knowledge/relationships` | Query `app_id` required, filters | Query relationships (app-scoped) |
| POST | `api/know/knowledge/relationships` | Body `app_id`, type, source/target | Create relationship (app-scoped) |
| GET | `api/know/knowledge/relationships/<id>` | Query `app_id` required | Get one relationship |
| PUT | `api/know/knowledge/relationships/<id>` | Body `app_id`, properties | Update relationship |

Skills-scoped queries: use `app_id=skills` (or the configured skills app id) on the query endpoint; Atlas and Neo4j are filtered by `app_id`; no separate skills code path.

### 2. Database and persistence

- **Django (MySQL):** `app_know.models.Knowledge` — no `app_id`; knowledge is global. No new migrations for multi-app (scoping is in Atlas/Neo4j and request params).
- **Atlas (MongoDB):** Collection `knowledge_summaries` with `knowledge_id`, `summary`, `app_id`, `source`, `ct`, `ut`. Unique index `(knowledge_id, app_id)`. Save/get/list/search are app-scoped via `app_id`.
- **Neo4j:** Knowledge and Entity nodes and all relationships carry `app_id`. Create/update/get/query and `get_related_by_knowledge_ids` use `app_id` in Cypher.

### 3. Repositories

- **summary_repo:** `save_summary`, `get_summary`, `list_summaries` by `knowledge_id` and `app_id`; `search_summaries_by_text(query, app_id, limit)` for logical query. Validation: non-empty `app_id` where required, query/length/limit bounds.
- **relationship_repo:** Create/update/get/query relationships by `app_id`; `get_related_by_knowledge_ids(knowledge_ids, app_id, limit)` for logical query. All nodes/edges app-scoped; validation for empty `app_id`, limit, offsets.

### 4. Services

- **KnowledgeService:** CRUD for knowledge (no app_id).
- **SummaryService / SummaryGenerator:** Generate and save summaries; get/list by `app_id`.
- **RelationshipService:** Create/update/get/query by `app_id`; validation for type-specific fields and limits.
- **LogicalQueryService:** (1) Atlas `search_summaries_by_text(query, app_id, limit)` → candidates; (2) when `app_id` present, Neo4j `get_related_by_knowledge_ids` → related; (3) merge and rank. Skills-scoped query is the same pipeline with `app_id=skills`.

### 5. Views and validation

- **KnowledgeSummaryView, KnowledgeSummaryListView:** `app_id` in query or body; validation and error mapping (`RET_MISSING_PARAM`, `RET_INVALID_PARAM`, etc.).
- **LogicalQueryView:** GET/POST with `query`/`q`, `app_id`, `limit`; validation for query length and limit; POST body parsed from `request.body` when needed.
- **RelationshipListView, RelationshipDetailView:** `app_id` required on list/detail and body where applicable; limit/offset and relationship_id validation; JSON body handling.

Errors are mapped to `RET_MISSING_PARAM`, `RET_INVALID_PARAM`, `RET_JSON_PARSE_ERROR`, `RET_DB_ERROR`, `RET_RESOURCE_NOT_FOUND` via `resp_err` / `resp_exception`; existing patterns preserved.

### 6. Tests

- **test_summary_repo.py:** save/get/list by `app_id`; empty `app_id` validation; list pagination; search_summaries_by_text validation and success.
- **test_summary_view.py:** get/post/list with `app_id`; missing/whitespace `app_id`; app_id coercion; invalid knowledge_id filter.
- **test_relationship_repo.py:** create/query/get/update by `app_id`; empty `app_id` raises; app_id mismatch returns None; get_related_by_knowledge_ids.
- **test_relationship_view.py:** list/detail/create/update require `app_id`; invalid relationship_id, offset, limit, JSON body; URL resolution and APIClient.
- **test_query_service.py:** validation (query/limit); Atlas-only; with `app_id` and Neo4j pipeline; `test_query_skills_app_id_uses_neo4j_pipeline` for `app_id=skills`; edge cases (missing knowledge_id, empty Atlas + Neo4j).
- **test_query_view.py:** GET/POST success with `app_id`; missing query; invalid limit; skills-scoped GET/POST with `app_id=skills` (service called with `app_id='skills'`); endpoint via client.

Run: `python manage.py test app_know.tests` (requires Django settings and DB for full run).

---

## Files touched (multi-application and skills-scoped)

| Round | Area | File |
|-------|------|------|
| 1 | Scope | `app_know/SCOPE_MULTI_APP_AND_SKILLS.md` — **new** |
| 2 | Tests | `app_know/tests/test_query_view.py` — skills-scoped (GET/POST app_id=skills, endpoint) |
| 2 | Tests | `app_know/tests/test_query_service.py` — `test_query_skills_app_id_uses_neo4j_pipeline` |
| 3 | Validation/errors | `app_know/services/knowledge_service.py` — coerce str; edge cases |
| 3 | Validation/errors | `app_know/views/relationship_view.py` — app_id required; limit/offset; body parsing; PUT app_id |
| 3 | Validation/errors | `app_know/views/query_view.py` — POST body from request.body |
| 3 | Tests | `app_know/tests/test_relationship_view.py` — invalid id/offset/limit/JSON; PUT missing app_id |
| 3 | Tests | `app_know/tests/test_knowledge_view.py` — description coercion |
| 3 | Tests | `app_know/tests/test_query_view.py` — POST body parsed |
| 3 | Tests | `app_know/tests/test_query_service.py` — atlas missing knowledge_id; atlas empty + Neo4j |
| 3 | Tests | `app_know/tests/test_summary_view.py` — app_id whitespace; invalid knowledge_id |
| 4 | Report | `app_know/REPORT_MULTI_APP_AND_SKILLS.md` — **new** (this file, generated) |

No files outside `app_know` were modified.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Add multi-application support (app_id or scope in config/request) | Done — app_id in query/body for summary, query, relationship APIs |
| Migrate skills-query into app_know; skills-scoped queries | Done — logical query with app_id=skills reuses Atlas + Neo4j pipeline |
| Existing knowledge CRUD and new relationship/summary/query APIs under app_know | Done — all under app_know at api/know/ |

---

*Report generated. Round 4 of 4. Multi-application support and skills-scoped queries implemented per requirement; output marked as generated.*
