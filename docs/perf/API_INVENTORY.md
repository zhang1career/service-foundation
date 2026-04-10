# HTTP API inventory (non-console apps)

**Baseline numbers:** [BASELINE.md](./BASELINE.md) (Locust command, Docker context, recorded percentiles).

Prefix from [service_foundation/urls.py](../../service_foundation/urls.py). Excludes `app_console` (`/console/`).

Use for perf baseline and Locust/k6 routing. **Auth**: many write paths require service registration / JWT; prefer **dict** and **health** endpoints for smoke load without secrets.

| App | URL prefix | Notable GET (low external cost) | Notes |
|-----|------------|--------------------------------|-------|
| app_aibroker | `/api/ai/` | `v1/health` | No auth. `dict?codes=…` needs valid codes. Text/embeddings POST hit upstream — mock in round 1. |
| app_cdn | `/api/cdn/2020-05-31/` | `distribution` (list) | Content `d/{id}/{path}` needs real distribution id. `dict` at `/api/cdn/dict`. |
| app_cms | `/api/cms/` | `{route}/{id}/` | Dynamic content routes; needs seeded data. |
| app_know | `/api/know/` | `dict?codes=…` | Most knowledge routes need auth + data. |
| app_mailserver | `/api/mail/` | `dict?codes=…` | Gated by `APP_MAILSERVER_ENABLED`. |
| app_notice | `/api/notice/` | `dict?codes=…` | `send` POST reaches brokers — mock for round 1. |
| app_oss | `/api/oss/` | `dict?codes=…`, `''` list buckets | Object paths need OSS config. |
| app_searchrec | `/api/searchrec/` | `health`, `dict?codes=…` | Search/recommend POST need `access_key` + reg — mock for round 1. |
| app_snowflake | `/api/snowflake/` | `id?bid=` | `dict?codes=…`. |
| app_user | `/api/user/` | `dict?codes=…` | Login/register POST — use test accounts only. |
| app_verify | `/api/verify/` | `dict?codes=…` | `request`/`check` need channel config. |

Shared **dict** query: `GET …/dict?codes=<comma-separated>` — use a known code (e.g. from tests: `aibroker_nested_param_type`).

## Environment flags (Django)

See `service_foundation/settings.py`: `APP_*_ENABLED` toggles inclusion of each app’s routes.
