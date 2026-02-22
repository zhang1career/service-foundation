# Scope: Knowledge summary generation (app_know)

**Generated.** This document confirms scope for the knowledge-summary feature per the requirement. Round 1 of 4.

## Requirement (summary)

- Implement **Python-based knowledge summary generation** (from title/description/content or external source).
- **Persist** generated summaries to **MongoDB Atlas** in app_know (define collection schema).
- Schema fields: e.g. **knowledge_id**, **summary text**, **app/scope**.
- Provide **generation trigger** (API or job).
- **Keep summaries in sync** with knowledge entities.

## Constraints

- Modify only files under **app_know** unless the requirement explicitly includes other paths.
- Follow existing patterns: APIView, Singleton service, repo layer, `resp_ok`/`resp_err`, `RET_*` codes.
- Validate inputs and handle errors gracefully.
- Add or update tests consistent with existing test patterns (TestCase, mocks where appropriate).

---

## 1. API endpoints (in scope)

| Method | Path | Purpose |
|--------|------|--------|
| **POST** | `api/know/knowledge/<id>/summary` or `api/know/knowledge/summaries/generate` | Trigger summary generation for one or more knowledge items. |
| **GET** | `api/know/knowledge/<id>/summary` or `api/know/knowledge/summaries?knowledge_id=&app_id=&...` | Get summary for a knowledge item or list/filter summaries (e.g. by knowledge_id, app/scope). |
| **GET** | `api/know/knowledge/summaries` | List summaries with optional filters (app_id/scope, knowledge_id, limit, offset). |

Exact paths and query/body params to be finalized in implementation; above captures “trigger (API)” and “read summaries” from the requirement.

---

## 2. Database / persistence

- **Store:** MongoDB Atlas (existing `app_know.conn.atlas`), database from config (e.g. `MONGO_ATLAS_DB`).
- **Collection:** One dedicated collection in app_know for summaries (e.g. `knowledge_summaries`).
- **Schema (document shape):**
  - `knowledge_id` (int/long): FK to knowledge entity (MySQL `knowledge.id`).
  - `summary` (string): generated summary text.
  - `app_id` or `scope` (string): app/scope for multi-tenant or scoping (align with existing relationship `app_id` where relevant).
  - Optional: `source` (e.g. `title_description`, `external`), `ct`/`ut` (created/updated timestamps), `_id` (ObjectId).
- **Indexes:** At least `(knowledge_id, app_id)` or equivalent for lookup and sync; consider uniqueness to enforce one summary per (knowledge_id, app_id) if required.

No Django model/migrations for MySQL for summaries; persistence is MongoDB-only in app_know.

---

## 3. Services

- **Summary generation service (Python):**
  - Inputs: knowledge_id and/or (title, description, content) or external source reference.
  - Produces summary text (e.g. rule-based or placeholder implementation in Round 1; can be extended later with LLM/external API).
  - Validates inputs; raises or returns errors for invalid/missing data.

- **Summary persistence service / repo:**
  - **Save:** upsert summary document into MongoDB (by knowledge_id + app/scope).
  - **Get:** by knowledge_id (and optionally app_id).
  - **List:** by app_id/scope, optional knowledge_id, pagination (limit, offset).
  - **Delete (optional):** when knowledge entity is deleted, to keep summaries in sync.

- **Sync with knowledge entities:**
  - On knowledge create/update: optionally trigger generation or mark summary stale.
  - On knowledge delete: remove or invalidate corresponding summary document(s).
  Sync can be implemented via API-triggered flow and/or a job (e.g. django-crontab) that (re)generates or cleans summaries; exact trigger (API vs job) to be implemented per requirement.

---

## 4. Dependencies (from requirement and codebase)

| Dependency | Role |
|------------|------|
| **MongoDB Atlas** | Persist summaries (existing `app_know.conn.atlas`, `AtlasClient`, `get_atlas_client`). |
| **Knowledge entity (MySQL)** | Source of title/description/metadata; `app_know.models.Knowledge`, `app_know.repos` (`get_knowledge_by_id`, `list_knowledge`). |
| **Python** | Summary generation logic (in-app; no new external API required for Round 1 unless specified). |
| **Generation trigger** | API (POST endpoint above) and/or job (e.g. management command or cron); at least one in scope. |
| **app_id / scope** | Reuse existing app-scoping pattern (e.g. from relationship APIs) for summary documents. |

Existing stack: `pymongo`, Django, DRF, `common.consts.response_const`, `common.utils.http_util` — no new third-party packages required for persistence and API unless we add an external summarization API later.

---

## 5. Tests (in scope)

- **Repo:** CRUD for summary documents in MongoDB (with mocked Atlas or in-memory/test DB if available).
- **Service:** Validation (missing knowledge_id, invalid app_id, etc.), success paths for generate/save/get/list, not-found and error paths.
- **Views:** Status codes and error payloads for invalid/missing params, successful trigger and get/list (pattern: `test_knowledge_view.py`, `test_relationship_view.py`).

---

## 6. Round 1 focus

For **Round 1**, implementation can prioritize:

- MongoDB collection schema and repo (save/get/list) for summaries.
- Summary generation service (Python) with inputs from Knowledge (title/description/content or stub).
- One trigger endpoint (e.g. POST to generate and persist) and one read endpoint (GET by knowledge_id or list).
- Basic validation and error handling.
- Tests for repo and service (and optionally view).

Sync on knowledge update/delete and job-based trigger can follow in later rounds if not required in Round 1.

---

*Scope confirmed from requirement; implementation to follow in app_know with no changes outside app_know unless explicitly required.*

---

## Round 2 (backend logic). Generated.

- **API routes:** `GET/POST api/know/knowledge/<id>/summary` (read / trigger generate), `GET api/know/knowledge/summaries` (list with app_id, knowledge_id, limit, offset).
- **DB:** MongoDB collection `knowledge_summaries`; repo `app_know.repos.summary_repo` (save_summary, get_summary, list_summaries, delete_by_knowledge_id).
- **Services:** `summary_generator.generate_summary(title, description, ...)`, `SummaryService.generate_and_save/get_summary/list_summaries/delete_summaries_for_knowledge`.
- **Sync:** On knowledge delete, `KnowledgeService.delete_knowledge` calls `SummaryService().delete_summaries_for_knowledge(knowledge_id)`.
- **Tests:** `test_summary_repo.py`, `test_summary_service.py`, `test_summary_view.py`. Run with Django: `python manage.py test app_know.tests.test_summary_repo app_know.tests.test_summary_service app_know.tests.test_summary_view` (requires MySQL for view tests; repo/service tests use mocks).

## Round 3 (validation, error handling, edge cases). Generated.

- **Input validation:** Repo: `summary` required string, max length 50k; `source` string or None; `offset`/`limit` required and validated. Generator: `title` required non-empty string; `max_length` positive integer. Service: `offset`/`limit` default 0/100 when None, type-checked. View: `entity_id` required, integer (reject float/empty); `app_id` coerced from number to string; list `limit`/`offset` range-checked.
- **Error handling:** ValueError mapped to RET_MISSING_PARAM / RET_INVALID_PARAM / RET_RESOURCE_NOT_FOUND; ParseError to RET_JSON_PARSE_ERROR; other exceptions to RET_DB_ERROR. Repo and service propagate PyMongoError.
- **Edge cases:** Empty string summary allowed; invalid knowledge_id returns None/0 where appropriate; generate_and_save when entity has empty title raises from generator; list_summaries with None offset/limit uses defaults.
- **Tests:** New/updated cases for repo (summary None/non-string/too long, source non-string, empty summary allowed, list offset/limit None); generator (title None/non-string, max_length 0/-1/None); service (empty title, list type and default tests); view (invalid entity_id, app_id number coercion, invalid JSON, list limit/offset validation).

## Round 4 (report and generated output). Generated.

- **Report:** Created `app_know/REPORT_KNOWLEDGE_SUMMARY.md` documenting all created or changed artifacts: summary_repo, summary_generator, summary_service, knowledge_service sync, summary_view, urls, tests. Spec compliance and files-touched listed; output marked **Generated**.
- **Output marking:** All new/updated deliverables (report, scope Round 4 section) are marked as generated. No files outside `app_know` were modified.
