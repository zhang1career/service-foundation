# 跨模块待办 / 改进备忘

## `common.services.http.executor.request_sync`

以下为该封装当前局限与可选改进（非必须立刻实施）。

- **成功路径固定打 INFO**：高 QPS 时日志量与磁盘 I/O 可能偏大；可按路径、`pool_name` 采样或降级级别。
- **无重试、无熔断**：网络抖动、429、5xx 等不会自动重试；若要做，需明确幂等性（尤其 POST）与退避策略。
- **`HttpCallError` 仅携带字符串**：调用方难以结构化区分超时、连接失败、TLS 错误等；可考虑包装 `httpx` 异常类型或错误码。
- **`get_http_client(..., timeout_sec=...)` 形参**：`client` 侧已不再根据该参数修改共享实例超时；该参数形同冗余，可删除并统一仅依赖 `request_sync(..., timeout_sec=)` → `client.request(timeout=...)`（需全库调用点核对）。
- **`json_body` 与 `data` 同时传入**：行为依赖 httpx 合并规则；调用方应避免二选一以外的用法，或在封装层显式校验互斥。
