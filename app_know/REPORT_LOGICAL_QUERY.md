# Report: Logical query interface (app_know)

**Generated.** This document was auto-generated to report what was created or changed for the logical query interface (Round 4 of 4).

---

## Summary

Implementation of the **logical query interface** in `app_know`: accept a natural-language or keyword query; (1) query **Atlas** by summary relevance (text search) to get candidate knowledge IDs; (2) run **Neo4j** graph reasoning (traversals) on those IDs to derive related knowledge/entities; (3) return **combined ranked results**. Exposed as **REST API** (GET and POST).

---

## What was created or changed

### 1. Atlas summary search (`app_know/repos/summary_repo.py`)

- **Changed.** Added `search_summaries_by_text(query, app_id=None, limit=100, atlas=None)`:
  - Case-insensitive `$regex` on `summary` for keyword/text relevance; optional `app_id` filter.
  - Returns list of dicts: `knowledge_id`, `summary`, `app_id`, `score` (1.0).
  - Validation: `query` required, non-empty string, length ≤ `QUERY_SEARCH_MAX_LEN` (2000); `limit` in 1..`LIMIT_LIST`; regex special characters escaped via `re.escape()` for safe search.
  - Raises `ValueError` for invalid inputs; propagates `ConnectionFailure`/`PyMongoError` on DB errors.
- Constant: `QUERY_SEARCH_MAX_LEN = 2000`.

### 2. Neo4j graph reasoning (`app_know/repos/relationship_repo.py`)

- **Changed.** Added `get_related_by_knowledge_ids(knowledge_ids, app_id, limit=200)`:
  - Cypher traversals: outgoing `(Knowledge)-[r]->(Entity|Knowledge)` and incoming `(Knowledge)-[r]->(Knowledge)` where `Knowledge.knowledge_id IN $ids`.
  - Returns list of dicts: `type` (knowledge|entity), `knowledge_id`, `entity_type`, `entity_id`, `source_knowledge_id`, `hop` (1); deduplicated by (type, id).
  - Validation: `app_id` required non-empty; `knowledge_ids` must be a list; `limit` in 1..`REL_LIST_LIMIT` (1000); filters to positive integer IDs (empty list returns []).
  - Raises `ValueError` for invalid inputs; propagates Neo4j exceptions.

### 3. Logical query service (`app_know/services/query_service.py`)

- **Created.** `LogicalQueryService` (Singleton):
  - `query(query, app_id=None, limit=None)`:
    - (1) Atlas: `search_summaries_by_text()` → candidate knowledge IDs with score, `source: "atlas"`, `hop: 0`.
    - (2) Neo4j: when `app_id` present and candidates non-empty, `get_related_by_knowledge_ids()` → related knowledge/entities with `source: "neo4j"`, `hop: 1`.
    - (3) Combine and rank: Atlas candidates first (by score), then Neo4j-related (by hop); deduplicate by knowledge_id / (entity_type, entity_id); cap by `limit`.
  - Validation: `_validate_query()` (required, string, non-empty, length ≤ QUERY_SEARCH_MAX_LEN); `_validate_limit()` (int in 1..LIMIT_LIST, default 50).
  - Returns `{ "data": [...], "total_num": N }`; each item has `type`, `knowledge_id`, `entity_type`, `entity_id`, `summary`, `score`, `source`, `hop`, optional `source_knowledge_id`.
  - Errors: re-raises `ValueError`; logs and re-raises Atlas/Neo4j exceptions.

### 4. REST API view (`app_know/views/query_view.py`)

- **Created.** `LogicalQueryView` (APIView):
  - **GET** `api/know/knowledge/query`: query params `query` or `q` (required), `app_id`, `limit`.
  - **POST** `api/know/knowledge/query`: JSON body `query` or `q` (required), `app_id`, `limit`.
  - Validation: query required and non-empty; query length ≤ QUERY_SEARCH_MAX_LEN; limit integer in 1..LIMIT_LIST (default 50).
  - Responses: `resp_ok(out)` on success; `resp_err(..., RET_MISSING_PARAM)` when query missing; `resp_err(..., RET_INVALID_PARAM)` for invalid limit/length; `resp_err(..., RET_JSON_PARSE_ERROR)` for invalid POST JSON; `resp_exception(..., RET_DB_ERROR)` when service raises.
  - Handles `ValueError`, `ParseError`, and generic `Exception`; logs warnings/exceptions.

### 5. URL configuration (`app_know/urls.py`)

- **Changed.** Added route:
  - `knowledge/query` → `LogicalQueryView` (name: `knowledge-query`).
  - (Mounted under `api/know/` in project.)

### 6. Tests

- **Created/updated.** All under `app_know/tests/`:
  - **test_summary_repo.py:** `search_summaries_by_text` – validation (query required/empty/type, limit, query too long), success with mock find, regex special chars escaped.
  - **test_relationship_repo.py:** `get_related_by_knowledge_ids` – empty app_id raises, empty/invalid ids return/raise, invalid limit raises, returns knowledge and entity (mocked Neo4j).
  - **test_query_service.py:** validation (query/limit, max length); Atlas-only; with app_id + Neo4j; combined ranking; Atlas empty / both empty; Atlas/Neo4j/ValueError propagation (mocked repos).
  - **test_query_view.py:** GET/POST success (mocked service); missing query; invalid limit and boundaries (1, LIMIT_LIST); query too long; empty POST body; invalid JSON; service raises → RET_DB_ERROR; `LogicalQueryEndpointTest` – URL resolve, GET/POST via APIClient.

Run: `python manage.py test app_know.tests.test_query_service app_know.tests.test_query_view app_know.tests.test_summary_repo app_know.tests.test_relationship_repo` (77 tests, all passing).

---

## Files touched (logical query only)

| Area    | File | Change |
|---------|------|--------|
| Repo    | `app_know/repos/summary_repo.py` | Added `search_summaries_by_text`, `_regex_escape`, `QUERY_SEARCH_MAX_LEN` |
| Repo    | `app_know/repos/relationship_repo.py` | Added `get_related_by_knowledge_ids` |
| Service | `app_know/services/query_service.py` | **New** – `LogicalQueryService` |
| View    | `app_know/views/query_view.py` | **New** – `LogicalQueryView` |
| URLs    | `app_know/urls.py` | Added `knowledge/query` |
| Tests   | `app_know/tests/test_summary_repo.py` | Added search tests |
| Tests   | `app_know/tests/test_relationship_repo.py` | Added get_related tests |
| Tests   | `app_know/tests/test_query_service.py` | **New** |
| Tests   | `app_know/tests/test_query_view.py` | **New** |
| Scope   | `app_know/SCOPE_LOGICAL_QUERY.md` | **New** – scope and rounds |
| Report  | `app_know/REPORT_LOGICAL_QUERY.md` | **New** – this file (generated) |

No files outside `app_know` were modified for this feature.

---

## API quick reference

| Method | Path | Body/Params | Purpose |
|--------|------|-------------|---------|
| GET    | `api/know/knowledge/query` | `query` or `q` (required), `app_id`, `limit` | Logical query via query string |
| POST   | `api/know/knowledge/query` | JSON: `query` or `q` (required), `app_id`, `limit` | Logical query via JSON body |

Success response: `{ "code": 0, "data": { "data": [...], "total_num": N } }`. Each result item: `type`, `knowledge_id`, `entity_type`, `entity_id`, `summary`, `score`, `source` (atlas|neo4j), `hop`, optional `source_knowledge_id`.

---

*Report generated. Round 4 of 4. Logical query interface implemented per requirement; all tests passing.*
