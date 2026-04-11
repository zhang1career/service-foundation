"""
Locust entry: smoke GETs across enabled apps (dict + health-style endpoints),
plus POST /api/snowflake/id.

Environment:
  HOST                 — base URL (also pass via Locust --host)
  DICT_CODES           — comma-separated dict codes (default: aibroker_nested_param_type)
  TEST_SNOWFLAKE_ACCESS_KEY — JSON body access_key for POST /api/snowflake/id (default: empty)
"""
from __future__ import annotations

import os

from locust import HttpUser, between, task


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return int(raw)


DICT_CODES = os.environ.get("DICT_CODES", "aibroker_nested_param_type")
TEST_SNOWFLAKE_ACCESS_KEY = os.environ.get("TEST_SNOWFLAKE_ACCESS_KEY", "")

W_DICT = _env_int("WEIGHT_DICT", 10)
W_HEALTH = _env_int("WEIGHT_HEALTH", 3)
W_SNOW = _env_int("WEIGHT_SNOWFLAKE", 2)


class SmokeUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(W_DICT)
    def dict_aibroker(self):
        self.client.get(
            "/api/ai/dict",
            params={"codes": DICT_CODES},
            name="/api/ai/dict",
        )

    @task(W_DICT)
    def dict_user(self):
        self.client.get(
            "/api/user/dict",
            params={"codes": DICT_CODES},
            name="/api/user/dict",
        )

    @task(W_DICT)
    def dict_know(self):
        self.client.get(
            "/api/know/dict",
            params={"codes": DICT_CODES},
            name="/api/know/dict",
        )

    @task(W_DICT)
    def dict_verify(self):
        self.client.get(
            "/api/verify/dict",
            params={"codes": DICT_CODES},
            name="/api/verify/dict",
        )

    @task(W_DICT)
    def dict_notice(self):
        self.client.get(
            "/api/notice/dict",
            params={"codes": DICT_CODES},
            name="/api/notice/dict",
        )

    @task(W_DICT)
    def dict_oss(self):
        self.client.get(
            "/api/oss/dict",
            params={"codes": DICT_CODES},
            name="/api/oss/dict",
        )

    @task(W_DICT)
    def dict_snowflake(self):
        self.client.get(
            "/api/snowflake/dict",
            params={"codes": DICT_CODES},
            name="/api/snowflake/dict",
        )

    @task(W_DICT)
    def dict_cdn(self):
        self.client.get(
            "/api/cdn/dict",
            params={"codes": DICT_CODES},
            name="/api/cdn/dict",
        )

    @task(W_DICT)
    def dict_searchrec(self):
        self.client.get(
            "/api/searchrec/dict",
            params={"codes": DICT_CODES},
            name="/api/searchrec/dict",
        )

    @task(W_HEALTH)
    def health_aibroker(self):
        self.client.get("/api/ai/v1/health", name="/api/ai/v1/health")

    @task(W_HEALTH)
    def health_searchrec(self):
        self.client.get("/api/searchrec/health", name="/api/searchrec/health")

    @task(W_SNOW)
    def snowflake_id(self):
        self.client.post(
            "/api/snowflake/id",
            json={"access_key": TEST_SNOWFLAKE_ACCESS_KEY},
            name="/api/snowflake/id",
        )
