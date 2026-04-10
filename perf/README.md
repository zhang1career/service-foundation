# Load and smoke tests

Targets **read-mostly** routes suitable for first-round baselines (no LLM / external broker calls). Set `HOST` to your running server, e.g. `http://127.0.0.1:8000` or Docker **`http://127.0.0.1:18041`** for `serv-fd`.

**Recorded baseline (command, environment, percentiles):** [docs/perf/BASELINE.md](../docs/perf/BASELINE.md).

## Locust

```bash
pip install -r requirements-dev.txt
export HOST=http://127.0.0.1:8000
export DICT_CODES=aibroker_nested_param_type
locust -f perf/locustfile.py
```

Open http://localhost:8089 and start a swarm, or headless:

```bash
locust -f perf/locustfile.py --headless -u 20 -r 5 -t 60s --host "$HOST"
```

Optional: `SNOWFLAKE_BID=1` (default), `WEIGHT_DICT=10` etc. to tune task mix.

## k6 (optional)

Requires [k6](https://k6.io/) installed on the machine (not a Python package).

```bash
export HOST=http://127.0.0.1:8000
k6 run perf/k6/dict-smoke.js
```

## Microbenchmarks (optional)

`requirements-dev.txt` includes `pytest-benchmark`. After `pip install -r requirements-dev.txt`, you can add small `benchmark` tests locally or run:

```bash
pytest path/to/test_module.py --benchmark-only
```
