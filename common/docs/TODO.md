# common — TODO

与 `common/services/http` 及出站调用相关的后续改进项（具体、可验收）。

## 出站策略（outbound policy）

- 为「允许访问的主机 / 前缀 / 解析结果」定义单一配置入口（例如 settings 或策略对象），在发起请求前校验 `url`；拒绝内网、链路本地、元数据地址等 SSRF 常见目标时给出明确错误码或异常类型。
- 明确是否允许 `file:`、`ftp:` 等非 HTTP(S) scheme；默认仅允许 `http`/`https`。
- 对跟随重定向设定统一策略（关闭跟随、或限制重定向次数与最终 URL 再次校验）；与 httpx 的 `follow_redirects` 行为对齐并文档化。
- 按业务池（`HttpClientPool`）覆盖策略差异时，用显式分支或注册表，避免长链 `or` 默认回退。

## 错误分型（error typing）

- 将 `HttpCallError` 细分为可恢复与不可恢复（例如超时、连接失败、TLS、非法 URL、策略拒绝），或保留统一外层类型但增加 `category` / `error_code` 字段供调用方与重试逻辑使用。
- 区分「传输层失败」与「已收到 HTTP 响应但 status 表示失败」：后者是否算错误由业务约定；若在 common 层封装，用独立类型或参数避免与连接错误混为一谈。
- 保证异常链完整：`raise ... from exc` 保留；日志或序列化时可选附带 `type(exc).__name__`，避免只存 `str(exc)` 丢失分类信息。

## 可观测性集成（observability）

- 在 `request_sync` / 异步任务执行路径上支持注入或从上下文读取 `trace_id` / `span_id`（OpenTelemetry 或项目现有 tracing），并写入日志字段。
- 为出站调用定义统一 metric 名称与标签（如 `pool`、`method`、status 或 `error_category`），便于 Prometheus 等聚合；避免高基数标签（完整 URL、未归一 path）。
- 日志与 metric 中的耗时统一使用同一时钟语义（如 `perf_counter` 毫秒），并与 Celery 任务日志中的 `elapsed_ms` 可对齐。

## 敏感日志处理（sensitive logging）

- 记录 URL 时默认剥离或哈希 `query` / `fragment`，或仅记录 `scheme` + `host` + 归一化 path；若需完整 URL 排障，通过开关或采样且仅限受控环境。
- `headers` 与 `params` 禁止整包落日志；对 `Authorization`、`Cookie`、`X-Api-Key` 等按名单脱敏为 `***` 或省略。
- 响应体、`json_body` 仅在 debug 且脱敏规则下记录；生产默认只记 status 与长度。
- 在文档中列出「禁止记录」字段清单，并在代码审查时对照。
