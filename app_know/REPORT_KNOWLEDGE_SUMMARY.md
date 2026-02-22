# Report: Knowledge summary generation (app_know)

**Generated.** This document was auto-generated to report what was created or changed for the knowledge-summary feature (Round 4 of 4).

---

## Summary

Implementation of **Python-based knowledge summary generation** in `app_know`: generate summaries from title/description/content (or external source), **persist** them to **MongoDB Atlas** in collection `knowledge_summaries`, provide **API trigger** (POST) and read endpoints (GET by id, GET list), and **keep summaries in sync** with knowledge entities (delete summaries when knowledge is deleted).

---

## What was created or changed

### 1. MongoDB repository (`app_know/repos/summary_repo.py`)

- **Created.** Atlas-backed repository for knowledge summaries:
  - **Schema:** `knowledge_id`, `summary`, `app_id`, `source`, `ct`, `ut`; unique index `(knowledge_id, app_id)`.
  - `save_summary(knowledge_id, summary, app_id, source=None)` – upsert by (knowledge_id, app_id); validates knowledge_id positive int, summary string ≤ 50k chars, app_id non-empty; raises `ValueError` or `PyMongoError`.
  - `get_summary(knowledge_id, app_id=None)` – get one summary; returns `None` if not found or invalid id.
  - `list_summaries(app_id, knowledge_id, offset, limit)` – list with filters; returns `(items, total)`; validates offset/limit.
  - `delete_by_knowledge_id(knowledge_id)` – delete all summaries for a knowledge_id (sync on knowledge delete); returns deleted count.
- Constants: `COLLECTION_NAME = "knowledge_summaries"`, `SUMMARY_STORAGE_MAX_LEN = 50_000`.

### 2. Summary generator (`app_know/services/summary_generator.py`)

- **Created.** Python-based summary generation:
  - `generate_summary(title, description=None, content=None, source_type=None, max_length=2000)` – builds summary from title/description/content/source_type; truncates to `max_length`; validates `title` required non-empty string, `max_length` positive int; raises `ValueError` on invalid input.
  - Rule-based implementation; can be extended with LLM or external API later.

### 3. Summary service (`app_know/services/summary_service.py`)

- **Created.** `SummaryService` (Singleton):
  - `generate_and_save(knowledge_id, app_id)` – loads knowledge by id, generates summary via `generate_summary`, upserts to MongoDB; validates knowledge_id and app_id; raises if knowledge not found.
  - `get_summary(knowledge_id, app_id=None)` – get one summary.
  - `list_summaries(app_id, knowledge_id, offset, limit)` – list with defaults offset=0, limit=100; returns `{ data, total_num, next_offset }`; validates types and range.
  - `delete_summaries_for_knowledge(knowledge_id)` – deletes all summaries for knowledge_id (used for sync); returns 0 for invalid id.

### 4. Sync with knowledge entities

- **Changed.** `app_know/services/knowledge_service.py`:
  - `delete_knowledge(entity_id)` – after deleting the MySQL knowledge entity, calls `SummaryService().delete_summaries_for_knowledge(knowledge_id=entity_id)` to remove MongoDB summaries; logs warning on failure but does not fail the delete.

### 5. REST API views (`app_know/views/summary_view.py`)

- **Created.** DRF APIView endpoints:
  - **KnowledgeSummaryView** (`GET` / `POST` `api/know/knowledge/<entity_id>/summary`):
    - `GET` – retrieve summary for knowledge `<entity_id>`; optional query `app_id`.
    - `POST` – trigger generation and persist; body `app_id` required.
  - **KnowledgeSummaryListView** (`GET` `api/know/knowledge/summaries`):
    - Query params: `app_id`, `knowledge_id`, `limit`, `offset` (limit/offset validated 1..LIMIT_LIST and ≥0).
  - Validation: `entity_id` required positive integer (reject float/empty); `app_id` coerced from number to string; `ValueError`/`ParseError`/other exceptions mapped to `RET_MISSING_PARAM`, `RET_INVALID_PARAM`, `RET_RESOURCE_NOT_FOUND`, `RET_JSON_PARSE_ERROR`, `RET_DB_ERROR`; responses via `resp_ok`/`resp_err`/`resp_exception`.

### 6. URL configuration (`app_know/urls.py`)

- **Changed.** Added routes:
  - `knowledge/<int:entity_id>/summary` → `KnowledgeSummaryView`
  - `knowledge/summaries` → `KnowledgeSummaryListView`
  - (Mounted under `api/know/` in project.)

### 7. Tests

- **Created.** Following existing app_know test patterns (Django `TestCase`, mocks for Atlas/MySQL where needed):
  - `app_know/tests/test_summary_repo.py` – repo: save/get/list/delete with mocked collection; validation (knowledge_id, summary None/non-string/too long, source non-string, offset/limit); edge cases (empty summary allowed, invalid knowledge_id returns None/0).
  - `app_know/tests/test_summary_service.py` – generator (title required, max_length validation, truncation); service: generate_and_save (success, not found, empty title), get_summary, list_summaries (defaults, type/range validation), delete_summaries_for_knowledge.
  - `app_know/tests/test_summary_view.py` – views: POST success/missing app_id/invalid entity_id; GET success/not found; list validation (limit/offset, app_id coercion); error codes; uses MySQL for Knowledge fixture where needed.

Run: `python manage.py test app_know.tests.test_summary_repo app_know.tests.test_summary_service app_know.tests.test_summary_view` (view tests require MySQL; repo and service tests use mocks).

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Python-based knowledge summary generation (title/description/content or external source) | Done – `summary_generator.generate_summary`; extensible for external source |
| Persist generated summaries to MongoDB Atlas in app_know | Done – collection `knowledge_summaries` via `app_know.conn.atlas` |
| Collection schema: knowledge_id, summary text, app/scope | Done – knowledge_id, summary, app_id, source, ct, ut |
| Generation trigger (API or job) | Done – POST `api/know/knowledge/<id>/summary` |
| Keep summaries in sync with knowledge entities | Done – on knowledge delete, `delete_summaries_for_knowledge` called from `KnowledgeService.delete_knowledge` |
| Validation and error handling | Done – ValueError → RET_*; PyMongoError/ConnectionFailure propagated; view validation for entity_id, app_id, limit, offset |

---

## Files touched (all under `app_know`)

- **Created:** `repos/summary_repo.py`, `services/summary_generator.py`, `services/summary_service.py`, `views/summary_view.py`, `tests/test_summary_repo.py`, `tests/test_summary_service.py`, `tests/test_summary_view.py`
- **Modified:** `urls.py` (summary routes), `services/knowledge_service.py` (sync on delete)

No changes were made outside `app_know`.

---

*Generated.*
