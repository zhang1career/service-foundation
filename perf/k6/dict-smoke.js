/**
 * k6 smoke: dict + health GETs. Requires k6 binary.
 *
 *   HOST=http://127.0.0.1:8000 k6 run perf/k6/dict-smoke.js
 */
import http from "k6/http";
import { check, sleep } from "k6";

const HOST = __ENV.HOST || "http://127.0.0.1:8000";
const DICT_CODES = __ENV.DICT_CODES || "aibroker_nested_param_type";

export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const paths = [
  `/api/ai/dict?codes=${encodeURIComponent(DICT_CODES)}`,
  `/api/user/dict?codes=${encodeURIComponent(DICT_CODES)}`,
  `/api/know/dict?codes=${encodeURIComponent(DICT_CODES)}`,
  "/api/ai/v1/health",
  "/api/searchrec/health",
];

export default function () {
  const path = paths[Math.floor(Math.random() * paths.length)];
  const res = http.get(`${HOST}${path}`);
  check(res, {
    "status is 2xx": (r) => r.status >= 200 && r.status < 300,
  });
  sleep(0.3);
}
