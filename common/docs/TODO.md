# common — TODO

按优先级排序（**P0** 最高）。条目合并了既有改进项与对 `common` 的严格评审结论；实施时以「可验收」为准。

---

## P0 — 安全与信任边界

1. **出站 URL 策略（SSRF）**  
   为「允许访问的主机 / 前缀 / 解析结果」定义单一配置入口（例如 settings 或策略对象），在发起请求前校验 `url`；拒绝内网、链路本地、元数据地址等 SSRF 常见目标时给出明确错误码或异常类型。

2. **出站 scheme 与重定向**  
   明确是否允许 `file:`、`ftp:` 等非 HTTP(S) scheme；默认仅允许 `http`/`https`。对跟随重定向设定统一策略（关闭跟随、或限制重定向次数与最终 URL 再次校验）；与 httpx 的 `follow_redirects` 行为对齐并文档化。

3. **`result_service` 动态调用边界**  
   `import_module` + `getattr` 执行任意模块函数依赖 `RESULT_INDEX_MAP`；明确仅允许服务端可信数据构造索引，禁止不可信输入直达；必要时加白名单或签名校验，并补测试。

4. **敏感日志（出站）**  
   记录 URL 时默认剥离或哈希 `query` / `fragment`，或仅记录 `scheme` + `host` + 归一化 path；若需完整 URL 排障，通过开关或采样且仅限受控环境。`headers` 与 `params` 禁止整包落日志；对 `Authorization`、`Cookie`、`X-Api-Key` 等按名单脱敏。响应体、`json_body` 仅在 debug 且脱敏规则下记录；生产默认只记 status 与长度。在文档中列出「禁止记录」字段清单。

5. **安全敏感路径的测试**  
   为 `HostValidationMiddleware` 等与主机/安全相关的逻辑补充单元测试（含 `ALLOWED_HOSTS`、端口、`SERVER_NAME` 等分支）。评审结论：中间件缺测风险高。

---

## P1 — 架构对齐与契约

6. **`AigcAPI` 归属**  
   `common/apis/aigc_api.py` 绑定 OpenAI 兼容上游与 `AIGC_*` 配置，与仓库规则「领域出站 HTTP 放在拥有该 API 的应用」不一致；择机迁到具体应用包，并在 `common` 仅保留通用传输原语（若仍需共享）。

7. **`django_util.post_to_dict` 契约**  
   实现依赖 `request.data`（DRF）；与命名「Django 通用」不符。应改名或拆分为 DRF 专用，并在文档中写明前置条件。

8. **出站池策略避免长链默认**  
   按业务池（`HttpClientPool`）覆盖策略差异时，用显式分支或注册表，避免长链 `or` 默认回退（与项目默认值规范一致）。

9. **公开 API 与异常信息**  
   复核 `DictCodesView` 等 `authentication_classes = []` 的端点是否符合产品安全假设；异常分支避免向客户端泄露内部细节（视 `resp_err` 实现收紧）。

---

## P2 — 错误模型、可测性与可观测性

10. **`HttpCallError` 分型**  
    将 `HttpCallError` 细分为可恢复与不可恢复（例如超时、连接失败、TLS、非法 URL、策略拒绝），或保留统一外层类型但增加 `category` / `error_code` 字段供调用方与重试逻辑使用。

11. **传输失败 vs HTTP 失败**  
    区分「传输层失败」与「已收到 HTTP 响应但 status 表示失败」：后者是否算错误由业务约定；若在 common 层封装，用独立类型或参数避免与连接错误混为一谈。

12. **异常链**  
    保证 `raise ... from exc` 完整；日志或序列化时可选附带 `type(exc).__name__`，避免只存 `str(exc)` 丢失分类信息。

13. **HTTP 路径可测性**  
    `request_sync` / `get_http_client` 强依赖 Django `settings` 与进程内连接池；`request_async` 经 Celery。单测需大量 patch 或偏集成；评估注入 httpx Client / 策略对象以降低耦合（与既有 HTTP TODO 协同）。

14. **可观测性**  
    在 `request_sync` / 异步任务执行路径上支持注入或从上下文读取 `trace_id` / `span_id`（OpenTelemetry 或项目现有 tracing），并写入日志字段。为出站调用定义统一 metric 名称与标签（如 `pool`、`method`、status 或 `error_category`），避免高基数标签（完整 URL、未归一 path）。日志与 metric 中的耗时统一使用同一时钟语义（如 `perf_counter` 毫秒），并与 Celery 任务日志中的 `elapsed_ms` 可对齐。

---

## P3 — 代码质量、全局状态与覆盖面

15. **`generic_code_for_ret` 启发式**  
    基于英文子串推断业务 ret 码易误判、难国际化；改为显式错误码或结构化错误来源，或缩小使用范围。

16. **`Singleton` 使用**  
    `AigcAPI`、各 `*Driver` 等使用 `Singleton`，测试需关心实例缓存与全局生命周期；新代码优先显式依赖注入或工厂，旧代码在修改时再评估是否收敛。

17. **缺测模块补测（抽样）**  
    评审中标记覆盖薄弱的区域包括但不限于：`aigc_api`、`milvus_driver`、`repos/knowledge_graph_repo`、`services/email`、`crawler/webpage_content_crawler`、`views`、`atlas_repl` 等；按业务优先级分批补测试或集成测试。

18. **包内分层说明**  
    `common` 同时包含纯工具、HTTP、驱动、DRF 视图、中间件、`repos` 等；在文档中写清依赖方向与误用风险，便于新人与审查。

---

## 说明

- **不触发对 `common` 的全量重构**；以上项在触及相关模块或设门禁时渐进完成即可。  
- **唯一适合单独立项的架构迁移**为 `AigcAPI` 迁出 `common`（若团队采纳该边界规则）。
