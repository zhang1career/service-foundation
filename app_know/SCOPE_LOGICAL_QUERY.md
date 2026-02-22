# Scope: Logical query interface (app_know)

**Generated.** Round 1 of 4. Confirms scope and implementation for the logical query interface per requirement. Round 2: backend logic verified; endpoint tests added. Round 3: input validation, error handling, and edge-case coverage added.

## Requirement (summary)

- Implement the **logical query interface**: accept a natural-language or keyword query.
- (1) **Query Atlas** by summary relevance (e.g. text search or embedding similarity) to get candidate knowledge IDs.
- (2) **Run Neo4j graph reasoning** (traversals, logic) on those IDs to derive related knowledge/entities.
- (3) **Return combined ranked results.** Expose as REST or internal API.

## Constraints

- Modify only files under **app_know** unless the requirement explicitly includes other paths.
- Follow existing patterns: APIView, Singleton service, repo layer, `resp_ok`/`resp_err`, `RET_*` codes.
- Validate inputs and handle errors gracefully.
- Add or update tests consistent with existing test patterns.

---

## 1. API endpoints (implemented)

| Method | Path | Purpose |
|--------|------|---------|
| **GET** | `api/know/knowledge/query?query=<q>&app_id=&limit=` | Logical query via query params (`query` or `q` required). |
| **POST** | `api/know/knowledge/query` | Logical query via JSON body: `query` or `q` (required), `app_id`, `limit`. |

---

## 2. Database / persistence

- **Atlas:** Reuses collection `knowledge_summaries`. No new collections. **Search:** `search_summaries_by_text(query, app_id, limit)` uses case-insensitive `$regex` on `summary` to get candidate knowledge IDs (Round 1: no embedding; can add later).
- **Neo4j:** Reuses existing graph (Knowledge, Entity nodes; RELATES_TO_ENTITY, RELATES_TO_KNOWLEDGE). **Reasoning:** `get_related_by_knowledge_ids(knowledge_ids, app_id, limit)` runs Cypher traversals (outgoing and incoming) to return related knowledge and entities.
- No new Django models or migrations.

---

## 3. Services and dependencies

- **summary_repo:** `search_summaries_by_text()` – Atlas text search for candidate IDs; validation (query required, non-empty, length ≤ QUERY_SEARCH_MAX_LEN; limit in 1..LIMIT_LIST); regex escape for safe search.
- **relationship_repo:** `get_related_by_knowledge_ids()` – Neo4j graph reasoning from candidate IDs to related knowledge/entities; validation (app_id required, knowledge_ids list, limit in 1..REL_LIST_LIMIT).
- **LogicalQueryService** (Singleton): `query(query, app_id, limit)` – (1) Atlas search → candidates with score; (2) Neo4j expansion when `app_id` present; (3) merge and rank (candidates first, then related by hop); returns `{ data, total_num }`.
- **LogicalQueryView:** GET/POST; parses `query`/`q`, `app_id`, `limit`; validates (query length ≤ QUERY_SEARCH_MAX_LEN, limit in 1..LIMIT_LIST); returns combined ranked results or validation/DB error payloads (RET_MISSING_PARAM, RET_INVALID_PARAM, RET_JSON_PARSE_ERROR, RET_DB_ERROR).

---

## 4. Tests (added/updated)

- **test_summary_repo:** `search_summaries_by_text` validation, success; query too long; regex special chars escaped.
- **test_relationship_repo:** get_related_by_knowledge_ids (empty app_id/ids, invalid ids, invalid limit, returns knowledge and entity); other relationship CRUD tests.
- **test_query_service:** Validation (query/limit, query max length); Atlas only; with app_id + Neo4j; combined ranking; Atlas empty, both empty; Atlas/Neo4j/ValueError propagation.
- **test_query_view:** GET/POST success, missing query, invalid limit, limit boundaries (1, LIMIT_LIST), query too long, empty POST body, invalid JSON, service raises → RET_DB_ERROR; **LogicalQueryEndpointTest:** URL resolve, GET/POST via APIClient.

Run: `python manage.py test app_know.tests.test_query_service app_know.tests.test_query_view app_know.tests.test_summary_repo app_know.tests.test_relationship_repo`

---

## 5. Files touched (Round 1)

| Area | File |
|------|------|
| Repo | `app_know/repos/summary_repo.py` – `search_summaries_by_text()` |
| Repo | `app_know/repos/relationship_repo.py` – `get_related_by_knowledge_ids()` |
| Service | `app_know/services/query_service.py` – **new** `LogicalQueryService` |
| View | `app_know/views/query_view.py` – **new** `LogicalQueryView` |
| URLs | `app_know/urls.py` – path `knowledge/query` |
| Tests | `app_know/tests/test_summary_repo.py`, `test_relationship_repo.py`, `test_query_service.py`, `test_query_view.py` – **new/updated** |
| Scope | `app_know/SCOPE_LOGICAL_QUERY.md` – **new** (this file) |

No files outside `app_know` were modified.

---

*Scope and implementation generated per requirement; Round 1 of 4. Round 2 of 4: endpoint tests added. Round 3 of 4: input validation (query max length, limit bounds), error handling (ValueError/ParseError/Exception → resp_err/resp_exception), edge-case tests; all tests passing. Round 4 of 4: report generated (REPORT_LOGICAL_QUERY.md).*
