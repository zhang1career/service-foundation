# Scope: Multi-application support and skills-scoped queries (app_know)

**Generated.** Round 1 of 4. Confirms scope: API endpoints, database models, services, and dependencies from the requirement. No files outside `app_know` are modified. Round 2 of 4: Backend logic verified; API routes, database operations, and services implemented; endpoint tests added (including skills-scoped query with app_id=skills). Round 3 of 4: Input validation, error handling, and edge-case coverage added (views, services, tests). Round 4 of 4: Report generated (REPORT_MULTI_APP_AND_SKILLS.md); output marked as generated.

## Requirement (summary)

- **Add multi-application support** (e.g. `app_id` or scope in config/request).
- **Migrate the local application's skills-query functionality into app_know:** implement skills-scoped queries (skills as one application), reusing Atlas summary relevance and Neo4j logic pipeline.
- **Ensure existing knowledge CRUD and new relationship/summary/query APIs are all under app_know.**

---

## 1. API endpoints (scope confirmed)

All endpoints live under `api/know/` (project mounts `app_know` at `api/know/`). Multi-application support is via `app_id` (and optionally scope) in request query or body where applicable.

| Method | Path | app_id / scope | Purpose |
|--------|------|----------------|---------|
| GET | `api/know/knowledge` | — | List knowledge (offset, limit, source_type) |
| POST | `api/know/knowledge` | — | Create knowledge |
| GET | `api/know/knowledge/<id>` | — | Get knowledge by id |
| PUT | `api/know/knowledge/<id>` | — | Update knowledge |
| GET | `api/know/knowledge/<id>/summary` | Query `app_id` | Get summary for one knowledge item |
| POST | `api/know/knowledge/<id>/summary` | Body `app_id` required | Trigger generate and save summary |
| GET | `api/know/knowledge/summaries` | Query `app_id`, knowledge_id, limit, offset | List summaries (app-scoped) |
| GET | `api/know/knowledge/query` | Query `query`/`q`, `app_id`, `limit` | Logical query (Atlas + Neo4j); skills-scoped when `app_id` e.g. `"skills"` |
| POST | `api/know/knowledge/query` | Body `query`/`q`, `app_id`, `limit` | Logical query (Atlas + Neo4j); skills-scoped when `app_id` set |
| GET | `api/know/knowledge/relationships` | Query `app_id` required, filters | Query relationships (app-scoped) |
| POST | `api/know/knowledge/relationships` | Body `app_id`, type, source/target | Create relationship (app-scoped) |
| GET | `api/know/knowledge/relationships/<id>` | Query `app_id` required | Get one relationship |
| PUT | `api/know/knowledge/relationships/<id>` | Body `app_id`, properties | Update relationship |

**Skills-scoped queries:** Call the logical query API with `app_id=skills` (or the configured application id for the skills app). Atlas and Neo4j are already filtered by `app_id`; no separate “skills” code path is required beyond using this parameter.

---

## 2. Database models and persistence (scope confirmed)

- **Django (MySQL):** `app_know.models.Knowledge` — knowledge metadata (id, title, description, source_type, metadata, ct, ut). No `app_id` on the model; knowledge is global; scoping is on relationships and summaries.
- **Migrations:** Existing migrations under `app_know` for `Knowledge`; no new migrations required for multi-application or skills-scoped query (scoping is in Atlas/Neo4j and request params).
- **Atlas (MongoDB):** Collection `knowledge_summaries`. Documents have `knowledge_id`, `summary`, `app_id`, `source`, `ct`, `ut`. Unique index `(knowledge_id, app_id)`. Search and list are app-scoped via `app_id`.
- **Neo4j:** Knowledge and Entity nodes and relationships (e.g. RELATES_TO_ENTITY, RELATES_TO_KNOWLEDGE) are app-scoped via `app_id` on nodes and edges. Query and “related by knowledge ids” use `app_id` in Cypher.

---

## 3. Services and dependencies (scope confirmed)

| Layer | Component | Role / dependency |
|-------|-----------|-------------------|
| Repo | `knowledge_repo` | MySQL CRUD for Knowledge (no app_id). |
| Repo | `summary_repo` | Atlas: save/get/list summaries by `knowledge_id` and `app_id`; `search_summaries_by_text(query, app_id, limit)` for logical query. |
| Repo | `relationship_repo` | Neo4j: create/update/get/query relationships by `app_id`; `get_related_by_knowledge_ids(knowledge_ids, app_id, limit)` for logical query. |
| Service | `KnowledgeService` | List/create/get/update knowledge (uses knowledge_repo). |
| Service | `SummaryService` / `SummaryGenerator` | Generate and save summaries; get/list by `app_id` (uses summary_repo, Knowledge). |
| Service | `RelationshipService` | Create/update/get/query relationships by `app_id` (uses relationship_repo). |
| Service | `LogicalQueryService` | Logical query: Atlas `search_summaries_by_text` → candidate IDs; Neo4j `get_related_by_knowledge_ids` when `app_id` present; merge and rank (uses summary_repo, relationship_repo). |
| View | KnowledgeListView, KnowledgeDetailView | Knowledge CRUD. |
| View | KnowledgeSummaryView, KnowledgeSummaryListView | Summary get/generate/list (app_id in query/body). |
| View | LogicalQueryView | GET/POST logical query (query/q, app_id, limit). |
| View | RelationshipListView, RelationshipDetailView | Relationship CRUD and query (app_id required). |

**External/config:** Atlas and Neo4j connections are used via `app_know.conn` (atlas, neo4j). Multi-application is request-level (`app_id` in config/request), not a separate connection per app.

---

## 4. Errors and validation (in scope)

- Repos and services validate `app_id` (required non-empty where applicable), `limit`/`offset`, and type-specific fields; raise `ValueError` or propagate DB exceptions.
- Views map validation/parse/DB errors to `RET_MISSING_PARAM`, `RET_INVALID_PARAM`, `RET_JSON_PARSE_ERROR`, `RET_DB_ERROR`, `RET_RESOURCE_NOT_FOUND` via `resp_err` / `resp_exception`; existing patterns preserved.

---

## 5. Tests (in scope)

- Existing test patterns in `app_know/tests/`: repo, service, and view tests (including `test_query_service`, `test_query_view`, `test_summary_repo`, `test_relationship_repo`, etc.).
- Round 2: Added skills-scoped query tests in `test_query_view.py` (GET/POST with `app_id=skills`, endpoint via client); added `test_query_skills_app_id_uses_neo4j_pipeline` in `test_query_service.py` to verify Atlas + Neo4j pipeline for skills app.

---

## 6. Files touched

| Round | Area | File |
|-------|------|------|
| 1 | Scope | `app_know/SCOPE_MULTI_APP_AND_SKILLS.md` — **new** (this file) |
| 2 | Tests | `app_know/tests/test_query_view.py` — skills-scoped query tests (GET/POST app_id=skills, endpoint) |
| 2 | Tests | `app_know/tests/test_query_service.py` — `test_query_skills_app_id_uses_neo4j_pipeline` |
| 3 | Validation / errors | `app_know/services/knowledge_service.py` — coerce description/source_type/title to str; edge cases |
| 3 | Validation / errors | `app_know/views/relationship_view.py` — app_id required (GET list/detail); limit/offset validation; _parse_relationship_id; _get_body JSON from request.body; PUT app_id required |
| 3 | Validation / errors | `app_know/views/query_view.py` — parse POST body from request.body when data empty (application/json) |
| 3 | Tests | `app_know/tests/test_relationship_view.py` — invalid relationship_id (0, non-integer); negative offset; limit over max; invalid JSON body; missing entity_type/target; PUT missing app_id |
| 3 | Tests | `app_know/tests/test_knowledge_view.py` — create with description as number (coerced to string) |
| 3 | Tests | `app_know/tests/test_query_view.py` — POST JSON body from request.body parsed |
| 3 | Tests | `app_know/tests/test_query_service.py` — atlas result missing knowledge_id skipped; atlas empty + Neo4j related |
| 3 | Tests | `app_know/tests/test_summary_view.py` — app_id whitespace-only; list with invalid knowledge_id (filter ignored) |
| 4 | Report | `app_know/REPORT_MULTI_APP_AND_SKILLS.md` — **new** (generated report of what was created or changed) |

No code or files outside `app_know` were modified. Round 3: input validation, error handling, and edge-case coverage added across views, services, and tests. Round 4: report generated; all output marked as generated.

---

## Round 4 (report and generated output). Generated.

- **Report:** Created `app_know/REPORT_MULTI_APP_AND_SKILLS.md` documenting what was created or changed for multi-application support and skills-scoped queries: API endpoints, persistence, repos, services, views, validation, and tests. Spec compliance and files-touched listed; output marked **Generated**.
- **Output marking:** All deliverables (this scope doc Round 4 line, REPORT_MULTI_APP_AND_SKILLS.md) are marked as generated. No files outside `app_know` were modified.

---

*Scope confirmation generated. Round 1 of 4. API endpoints, database models, services, and dependencies confirmed against the requirement. Round 2 of 4: Backend logic verified; endpoint tests added for skills-scoped query. Round 3 of 4: Input validation, error handling, and edge-case tests added. Round 4 of 4: Report generated; output marked as generated. Run tests with `python manage.py test app_know.tests` (requires Django settings and DB for full run).*
