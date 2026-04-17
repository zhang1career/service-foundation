# `common` P2 可观测与错误模型评审

对照 `docs/plan/REVIEW_common.md` **第 7 节「建议执行顺序」**中 **P2 可观测与错误模型** 的三项：`HttpCallError` 分型、异常链、`request_sync` 可注入客户端（若立项）。并扩展对照 `common/docs/TODO.md` **P2**（§10～14）中与传输层错误、可测性、可观测性一致的表述。评价维度与 `REVIEW_common.md` **§1～3** 一致，结论采用「通过 / 待改进 / 阻塞」。

---

## 1. `HttpCallError` 分型（`common/services/http/errors.py` 及调用约定）

### 在架构中的角色

- 表示 **出站 HTTP 传输失败**（连接、超时、TLS 等 `httpx.HTTPError`），由 `request_sync` 在 `except httpx.HTTPError` 中抛出；**不**用于「已收到响应但 `status_code` 非成功」——后者由调用方根据 `httpx.Response` 自行处理，与 `common/docs/TODO.md` P2-11「传输失败 vs HTTP 失败」在 common 层的分工一致。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 当前仅为 `RuntimeError` 子类，无 `category` / `error_code`、无可恢复性标记；消息依赖 `str(httpx异常)`。调用方（如 Celery `sync_call_task`）无法按失败类型做差异化重试或熔断，与 `REVIEW_common.md` §7 P2、`TODO.md` P2-10 **未落地**。 |
| **独立性** | 类型本身无 Django 依赖；语义清晰。 |
| **边界清晰度** | 与「业务 HTTP 语义错误」分离合理；**待改进** 在于缺少结构化分型后，与 `distributed_tasks` 中 `autoretry_for=(HttpCallError,)` 组合时，**所有** `HttpCallError` 均被同等重试，无法区分永久失败（如错误 URL）与瞬时失败。 |
| **性能** | 无额外开销。 |
| **安全** | 无敏感字段专用处理；异常消息可能含上游片段，属通用边界问题。 |

### 结论

**待改进**（非阻塞）。与 `TODO.md` P2-10 一致：宜增加子类或 `category` / `error_code`，供重试策略与监控标签使用。

---

## 2. 异常链（`common/services/http/executor.py`）

### 在架构中的角色

- `request_sync` 在捕获 `httpx.HTTPError` 时使用 `raise HttpCallError(str(exc)) from exc`，保留 **PEP 3134** 因果链，便于 `__cause__` 追溯与日志系统展开。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 异常链完整；失败日志记录 `type(exc).__name__`，避免仅依赖 `str(exc)` 时完全丢失类型信息，与 `TODO.md` P2-12 方向一致。 |
| **独立性** | — |
| **边界清晰度** | — |
| **性能** | — |
| **安全** | — |

### 测试

- `common/tests/services/http/test_executor.py` 中 `test_request_sync_http_error_preserves_cause` 断言 `ctx.exception.__cause__ is inner`。

### 结论

**通过**。

---

## 3. `request_sync` 可注入客户端 / 可测性（`executor.py` + `client.py`）

### 在架构中的角色

- `request_sync` 固定调用 `get_http_client(pool_name=..., timeout_sec=...)` 获取进程内池化 `httpx.Client`；`get_http_client` 依赖 Django `settings`（`HTTPX_*`）与模块级 `_CLIENTS` 字典。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 无 `client=`、`get_http_client=` 等注入参数；可测性依赖对 `get_http_client` 或 `request_sync` 的 `patch`（`common/tests/services/http/test_executor.py` 采用前者），与 `REVIEW_common.md` §7「若立项」、`TODO.md` P2-13 **评估注入** 尚未在 API 层落实。 |
| **独立性** | 单测已能通过 mock `get_http_client` 避免真实网络；**集成/契约测试**仍与 settings、全局池耦合。 |
| **边界清晰度** | 传输层集中在一处，职责清楚；注入能力属于**可测性与部署灵活性**增强，不改变「common 不绑具体业务 API」的边界。 |
| **性能** | 连接池复用合理；与本节无关。 |
| **安全** | — |

### 结论

**待改进**（立项项）。当前工程上可用 patch 覆盖；若团队希望减少全局 patch、或并行测试隔离池状态，再引入可选注入与 `TODO.md` P2-13 对齐。

---

## 4. 可观测性（与 P2 同域的增量说明）

`REVIEW_common.md` §7 仅列三项；`TODO.md` P2-14 对同一域补充了 trace/metric 要求，此处一并简评以免与「错误模型」脱节。

| 项 | 现状 | 与 `TODO.md` P2-14 |
|----|------|---------------------|
| 同步成功路径 | `[http_call] mode=sync pool=… method=… status=… elapsed_ms=… url=…` | `elapsed_ms` 与 `perf_counter` 一致；**无** `trace_id` / `span_id` 字段。 |
| 同步失败路径 | `warning`：`error=<类型名>`、`elapsed_ms`、`url` | 类型名有利于粗分；仍无分布式追踪键。 |
| 指标 | 未见统一 metric API | 未落地。 |
| 高基数 | 日志含完整 `url` | 与「避免高基数标签」的 metric 建议需区分：日志用于排障可接受，**若**将同样维度写入 metric 则需归一化 path/host。 |

**结论**：**待改进**（与错误分型、注入并列的产品/基建项，非单点代码缺陷）。

---

## 5. 总表（本节范围）

| 主题 | 结论 |
|------|------|
| `HttpCallError` 分型与重试粒度 | **待改进** |
| 异常链与失败日志中的异常类型名 | **通过** |
| `request_sync` 可注入客户端 | **待改进**（若立项） |
| Trace / 统一 metrics | **待改进**（见 `TODO.md` P2-14） |
