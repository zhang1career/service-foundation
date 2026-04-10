# Performance baseline (smoke, dict + health)

This file records **comparable** load-test settings so a second run can be diffed fairly. Update the **Results** section when you re-run with the same command.

## Record

| Field | Value |
|-------|--------|
| Date | 2026-04-10 |
| Target | `http://127.0.0.1:18041` (Docker: `serv-fd`, image `service_foundation:latest`, host port **18041** → container **8000**) |
| HTTP stack | Django `runserver` via [`docker-entrypoint.sh`](../../docker-entrypoint.sh) (dev server; not gunicorn multi-worker). Optional same-container SMTP/IMAP if `START_MAIL_SERVER=true`. |
| Locust file | [`perf/locustfile.py`](../../perf/locustfile.py) |
| `DICT_CODES` | `aibroker_nested_param_type` (default in locustfile; override via env) |

## Command (fixed for regression)

```bash
locust -f perf/locustfile.py --headless -u 20 -r 5 -t 60s --host http://127.0.0.1:18041
```

| Parameter | Meaning |
|-----------|---------|
| `-u 20` | 20 concurrent users |
| `-r 5` | spawn 5 users/s until 20 |
| `-t 60s` | total duration 60s |

**Regression rule:** change only app code, settings, or DB; keep this command and host unless you intentionally change the scenario (then add a new dated section below).

## Results (2026-04-10 — run 1, before dict cache)

Approximate response time percentiles from Locust (unit: **ms**). Total requests **899**.

| Name | 50% | 95% | 99% | # reqs |
|------|-----|-----|-----|--------|
| GET /api/ai/dict | 4 | 7 | 16 | 97 |
| GET /api/ai/v1/health | 4 | 6 | 6 | 24 |
| GET /api/cdn/dict | 4 | 6 | 6 | 80 |
| GET /api/know/dict | 4 | 6 | 7 | 104 |
| GET /api/notice/dict | 4 | 6 | 9 | 78 |
| GET /api/oss/dict | 4 | 6 | 17 | 86 |
| GET /api/searchrec/dict | 4 | 6 | 15 | 87 |
| GET /api/searchrec/health | 4 | 7 | 13 | 30 |
| GET /api/snowflake/dict | 4 | 10 | **74** | 97 |
| GET /api/snowflake/id | 4 | 6 | 6 | 15 |
| GET /api/user/dict | 4 | 6 | 6 | 109 |
| GET /api/verify/dict | 4 | 7 | 12 | 92 |
| **Aggregated** | 4 | 6 | **74** | 899 |

### Notes

- **`/api/snowflake/dict`** showed a heavier **99%** tail than other `dict` routes in the first baseline (same `DictCodesView` code path — likely first-hit bundled import + repeated `to_dict_list()` work).
- Median **~4 ms** for most routes under this load; differences show up in high percentiles.

### Optimization applied (2026-04-10, post-baseline)

- [`get_dict_by_codes`](../../common/dict_catalog/registry.py): `functools.lru_cache(maxsize=256)` for identical `codes` strings; [`clear_dict_registry_for_tests`](../../common/dict_catalog/registry.py) calls `cache_clear()`.
- [`service_foundation/settings.py`](../../service_foundation/settings.py): `warm_dict_catalog_bundled()` at end of settings import to load [`common.dict_catalog.bundled`](../../common/dict_catalog/bundled.py) early.
- **Run 3+:** [`prime_http_dict_cache()`](../../common/dict_catalog/warmup.py) runs after `dict_registration` imports — in [`app_verify.apps`](../../app_verify/apps.py) when `APP_VERIFY_ENABLED`, else in [`app_user.apps`](../../app_user/apps.py). Primes `DICT_HTTP_PRIME_CODES` (default matches Locust smoke: `aibroker_nested_param_type`) so the first HTTP client hit is not the first `get_dict_by_codes` resolution.

## Results (2026-04-10 — run 2, after dict `lru_cache` + bundled warm)

Same Locust command as above. Total requests **890**.

| Name | 50% | 95% | 99% | # reqs |
|------|-----|-----|-----|--------|
| GET /api/ai/dict | 4 | 8 | 15 | 105 |
| GET /api/ai/v1/health | 4 | 31 | 31 | 20 |
| GET /api/cdn/dict | 4 | 9 | 30 | 87 |
| GET /api/know/dict | 4 | 13 | 47 | 83 |
| GET /api/notice/dict | 4 | 7 | 14 | 103 |
| GET /api/oss/dict | 4 | 8 | 27 | 86 |
| GET /api/searchrec/dict | 4 | 8 | 15 | 99 |
| GET /api/searchrec/health | 4 | 8 | 17 | 31 |
| GET /api/snowflake/dict | 4 | 14 | **47** | 87 |
| GET /api/snowflake/id | 5 | 39 | 39 | 19 |
| GET /api/user/dict | 4 | 25 | 48 | 78 |
| GET /api/verify/dict | 4 | 12 | **120** | 92 |
| **Aggregated** | 4 | 10 | **120** | 890 |

### Run 1 vs run 2 (same scenario, short runs)

- **Median (50%)** stays ~4–5 ms for most `dict` routes; load profile is comparable (#reqs within ~10%).
- **`/api/snowflake/dict` 99%:** 74 → **47** ms (fewer extreme tail requests on that name).
- **Aggregated 99%:** 74 → **120** ms — dominated by new tails on **`/api/verify/dict`** (120 ms) and higher tails on **`/api/ai/v1/health`**, **`/api/snowflake/id`**, **`/api/user/dict`**, not by a single shared dict path. With **60s** runs and **~20** samples per endpoint name, high percentiles are noisy; treat as **inconclusive for “overall regression”** unless repeated on an idle host or longer runs.
- **Next:** If chasing tails, re-run Locust 3× back-to-back and compare; optionally profile **`/api/verify/dict`** (same `DictCodesView` as others) under Docker CPU pinning.

## Results (2026-04-10 — run 3, after `prime_http_dict_cache`)

Same Locust command as above. Total requests **884**.

| Name | 50% | 95% | 99% | # reqs |
|------|-----|-----|-----|--------|
| GET /api/ai/dict | 4 | 6 | 7 | 85 |
| GET /api/ai/v1/health | 4 | 5 | 14 | 23 |
| GET /api/cdn/dict | 4 | 7 | 15 | 102 |
| GET /api/know/dict | 4 | 9 | 13 | 77 |
| GET /api/notice/dict | 4 | 7 | 15 | 99 |
| GET /api/oss/dict | 4 | 6 | **87** | 93 |
| GET /api/searchrec/dict | 4 | 7 | 25 | 84 |
| GET /api/searchrec/health | 4 | 7 | 15 | 43 |
| GET /api/snowflake/dict | 4 | 12 | 18 | 77 |
| GET /api/snowflake/id | 4 | **66** | 66 | 20 |
| GET /api/user/dict | 4 | 6 | 15 | 91 |
| GET /api/verify/dict | 4 | 8 | **18** | 90 |
| **Aggregated** | 4 | 7 | **15** | 884 |

### Run 2 vs run 3

- **Aggregated 99%:** 120 → **15** ms — run 2’s high tail was likely **noise** on short runs; run 3 aligns better with run 1’s overall shape.
- **`/api/verify/dict` 99%:** 120 → **18** ms (same code path as other `dict` routes; confirms run 2 outlier).
- **Largest tails in run 3:** **`/api/oss/dict`** (up to **87** ms at high percentiles) and **`/api/snowflake/id`** (**66** ms at 95–100%). Worth profiling separately (OSS vs DB/clock path), not shared `DictCodesView`.

## Next run (template)

Copy this block and fill **Date** and the table after each regression.

```markdown
## Results (YYYY-MM-DD)

Command: (same as above unless scenario changed)

| Name | 50% | 95% | 99% | # reqs |
|------|-----|-----|-----|--------|
| ... | | | | |
```

## See also

- [API_INVENTORY.md](./API_INVENTORY.md) — route map for non-console apps.
- [perf/README.md](../../perf/README.md) — Locust/k6 usage.
