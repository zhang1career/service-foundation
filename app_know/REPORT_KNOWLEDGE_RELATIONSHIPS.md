# Report: Neo4j persistence for knowledge relationships (app_know)

**Generated.** This document was auto-generated to report what was created or changed for the knowledge-relationship feature.

---

## Summary

Design and implementation of **Neo4j persistence for knowledge relationships** in `app_know`: storing **knowledge–entity** and **knowledge–knowledge** relationships (nodes and edges), with create/update/query APIs, using the existing app_know Neo4j client and **app-scoped multi-application support** (via `app_id` on all nodes and edges).

---

## What was created or changed

### 1. Models and constants (`app_know/models/relationships.py`)

- **Created.** Neo4j relationship models and constants:
  - Node labels: `Knowledge`, `Entity`
  - Relationship types: `RELATES_TO_ENTITY`, `RELATES_TO_KNOWLEDGE`
  - App-scoping: `APP_ID_PROP` used on all nodes and edges
  - Dataclasses: `RelationshipCreateInput`, `RelationshipUpdateInput`, `RelationshipQueryInput`, `RelationshipQueryResult`

### 2. Neo4j persistence / repository (`app_know/repos/relationship_repo.py`)

- **Created.** Repository layer using `app_know.conn.neo4j.get_neo4j_client()`:
  - `create_relationship(inp)` – creates or upserts a knowledge–entity or knowledge–knowledge relationship; ensures source/target nodes exist; validates `app_id`, `source_knowledge_id`, and type-specific fields
  - `update_relationship_by_id(app_id, relationship_id, properties)` – updates relationship by Neo4j internal id; enforces `app_id` on the relationship
  - `get_relationship_by_id(app_id, relationship_id)` – get one relationship by id; returns `None` if not found or `app_id` mismatch
  - `query_relationships(inp)` – query by `app_id` and optional filters (`knowledge_id`, `entity_type`, `entity_id`, `relationship_type`, `limit`, `offset`); returns `(list of RelationshipQueryResult, total count)`
  - All nodes and edges are app-scoped via `app_id` (multi-application support).

### 3. Service layer (`app_know/services/relationship_service.py`)

- **Created.** `RelationshipService` (Singleton) with validation:
  - `create_relationship(...)` – validates `app_id`, `relationship_type`, `source_knowledge_id`; for `knowledge_entity`: `entity_type`, `entity_id`; for `knowledge_knowledge`: `target_knowledge_id`; length limits for `app_id`, `entity_type`, `entity_id`
  - `update_relationship(...)` – validates `app_id`, `relationship_id`, non-empty `properties`; returns error when relationship not found or `app_id` mismatch
  - `get_relationship(...)` – get by id; returns `None` when not found or `app_id` mismatch
  - `query_relationships(...)` – validates `app_id`, `limit`, `offset`, optional filters; returns `{ data, total_num, next_offset }`

### 4. REST API views (`app_know/views/relationship_view.py`)

- **Created.** DRF APIView endpoints:
  - **RelationshipListView**
    - `GET /api/know/knowledge/relationships` – query relationships (query params: `app_id` required, `knowledge_id`, `entity_type`, `entity_id`, `relationship_type`, `limit`, `offset`)
    - `POST /api/know/knowledge/relationships` – create relationship (body: `app_id`, `relationship_type`, `source_knowledge_id`; for `knowledge_entity`: `entity_type`, `entity_id`; for `knowledge_knowledge`: `target_knowledge_id`; optional `properties`)
  - **RelationshipDetailView**
    - `GET /api/know/knowledge/relationships/<relationship_id>` – get one relationship (query param: `app_id` required)
    - `PUT /api/know/knowledge/relationships/<relationship_id>` – update relationship (body: `app_id`, `properties`)
  - Errors mapped to `RET_MISSING_PARAM`, `RET_INVALID_PARAM`, `RET_RESOURCE_NOT_FOUND`, `RET_DB_ERROR`, `RET_JSON_PARSE_ERROR`; validation and exceptions handled with appropriate HTTP 200 + error payloads.

### 5. URL configuration (`app_know/urls.py`)

- **Changed.** Added routes:
  - `knowledge/relationships` → `RelationshipListView`
  - `knowledge/relationships/<int:relationship_id>` → `RelationshipDetailView`
  - (Mounted under `api/know/` in project `service_foundation/urls.py`.)

### 6. Tests

- **Created.** Following existing app_know test patterns (Django `TestCase`, mocks for Neo4j):
  - `app_know/tests/test_relationship_repo.py` – repo: create (knowledge_entity / knowledge_knowledge, validation, unknown type), get_by_id (not found, app_id mismatch, empty/zero/negative id), update_by_id (success, not found, invalid props), query (empty app_id, results + total)
  - `app_know/tests/test_relationship_service.py` – service: create/update/query validation (app_id, relationship_type, entity_type/entity_id, target_knowledge_id, limits, offset, positive int), success paths, not-found and error paths
  - `app_know/tests/test_relationship_view.py` – views: list create/query validation and success; detail get/put validation and success; URL resolution; integration-style tests with `APIClient` and error codes

All **65** relationship tests pass via `python manage.py test app_know.tests.test_relationship_*`.

---

## Spec compliance

| Requirement | Status |
|-------------|--------|
| Neo4j persistence for knowledge relationships | Done – repo uses Neo4j for nodes and edges |
| Store knowledge–entity and knowledge–knowledge relationships (nodes and edges) | Done – `Knowledge`/`Entity` nodes; `RELATES_TO_ENTITY` / `RELATES_TO_KNOWLEDGE` edges |
| Expose create/update/query APIs | Done – POST create; PUT update; GET list + GET by id |
| Use existing app_know Neo4j client | Done – `app_know.conn.neo4j.get_neo4j_client()` only |
| Multi-application (app-scoped labels or namespace) | Done – `app_id` on all nodes and edges; all queries filtered by `app_id` |

---

## Files touched (all under `app_know`)

- **Created:** `models/relationships.py`, `repos/relationship_repo.py`, `services/relationship_service.py`, `views/relationship_view.py`, `tests/test_relationship_repo.py`, `tests/test_relationship_service.py`, `tests/test_relationship_view.py`
- **Modified:** `urls.py` (added relationship routes)

No changes were made outside `app_know` for this feature (project `service_foundation/urls.py` already included `app_know` at `api/know/`).

---

*Generated.*
