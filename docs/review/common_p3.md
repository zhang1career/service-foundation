# `common` P3 质量评审

对照 `docs/plan/REVIEW_common.md` **第 7 节「建议执行顺序」**中 **P3 质量** 的三项：`generic_code_for_ret`、Singleton 使用收敛、缺测模块按业务优先级补全。并扩展对齐 `common/docs/TODO.md` **§P3（15～18）** 中与同一主题相关的表述。评价维度与 `REVIEW_common.md` **§1～3** 一致，结论采用「通过 / 待改进 / 阻塞」。

---

## 1. `generic_code_for_ret`（`common/exceptions/base_exception.py`）

### 在架构中的角色

- 根据 **异常/提示字符串**（转小写后）是否包含英文子串 `"not found"`、`"required"`、`"cannot be empty"`、`"missing"`、`"non-empty"` 等，推断应返回的 **业务 ret 码**；否则返回调用方传入的 `code_by_default`（默认 `RET_OK`）。
- **调用方不在 `common` 内**：当前实际使用集中在 `app_know` 多个视图（`summary_view`、`query_view`、`relation_extract_view`、`relationship_view`），通过 `generic_code_for_ret(...)[0]` 只取 **码**，`message` 仍多为 `str(e)` 原样。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 启发式 **仅覆盖英文关键词**；中文或其它语言错误信息会落到默认码，与「用户可见语言」不一致。子串匹配易 **误判**（例如正文含 “not found” 但语义并非资源缺失）。返回元组第二元素为 **小写后的 `m`**，与入参 casing 不一致，若将来有调用方使用 `[1]` 需注意。 |
| **独立性** | 纯函数、无全局副作用；可单测，但 **`common/tests/` 中未见** 针对该函数或 `CheckedException`/`http_status_for_ret` 的用例（与 `REVIEW_common.md` §5.8 建议的显式映射优先方向相比，**测试缺口**）。 |
| **边界清晰度** | 放在 `exceptions` 中与异常模型相邻合理；**契约未文档化**（何种消息应走启发式、何种应显式传 `ret_code`）。 |
| **性能** | 短字符串扫描，可忽略。 |
| **安全** | 不直接引入注入；间接风险是 **错误码与对外 message 不一致** 时误导客户端行为，属质量/产品问题。 |

### 与 `http_status_for_ret` 的附带观察（同文件）

- 对 `200 <= ret_code < 300` 映射为 **403** 的语义较反常（通常成功码不应出现在 ret 通道）；若属历史兼容，宜注释说明，避免误用。**非 P3 必改项**，但与「错误模型清晰」同一主题相关。

### 结论

**待改进**。与 `common/docs/TODO.md` P3-15 一致：宜 **缩小使用范围**、改为 **显式错误码/结构化错误**，或至少 **补充单测** 固定关键短语行为并文档化局限；国际化场景下应 **避免** 依赖英文子串推断。

---

## 2. `Singleton` 使用收敛（`common/components/singleton.py` 及引用点）

### 在架构中的角色

- 元类 `_Singleton` 按 `(args + tuple(sorted(kwargs.items())))` 的 **哈希键** 缓存「每类每参组合」一个实例；`Singleton` 为可直接继承的基类。
- **`common` 内继承 `Singleton` 的类**（检索结果）：`MongoDriver`、`LocalMilvusDriver`、`Neo4jDriver`、`AigcAPI`。均为 **长生命周期、重资源**（连接、HTTP 客户端池）对象，与「进程内复用」目标一致。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | `common/tests/components/test_singleton.py` 覆盖了 **多参、kwargs 顺序、边界字符串** 等身份一致性，**元类行为**可视为有基础回归保障。 |
| **独立性** | 全局实例表 `_Singleton._instances` 跨子类共享结构；测试需 `clear` 或进程隔离时注意 **类间不串**（当前测例用独立子类，合理）。若某 `Singleton` 子类构造参数含 **不可哈希** 对象，`hash(args + …)` 会在运行时失败——当前驱动/`AigcAPI` 入参多为可哈希类型，**风险较低但未在类型/文档中声明**。 |
| **边界清晰度** | 与 `TODO.md` P3-16 一致：**新代码** 宜优先 **工厂/显式依赖注入**；现有四类属渐进收敛对象，**未**要求一次性重构。`AigcAPI` 的 Singleton 与 **P1「迁出 common」** 决策正交：迁出后仍可保留单例或改为应用内 bean。 |
| **性能** | 避免重复建立连接，符合驱动层预期。 |
| **安全** | 非安全敏感；多租户/多配置进程若错误共用一个 `(cls, args_hash)` 实例会导致 **串配置**，属部署与调用约定问题。 |

### 结论

**通过**（就 **实现 + 元类级单测** 而言）。**待改进**（就 **使用策略** 而言）：引用面已覆盖 API 与三类驱动，**未滥用**；后续新增 `Singleton` 子类应按 P3-16 **控制增量**，并在集成测试中关注 **生命周期**（关闭连接、测试间清理）。

---

## 3. 缺测模块补全（对齐 `REVIEW_common.md` §6 与 `TODO.md` P3-17）

### 范围说明

- 计划文档列出的 **覆盖薄或缺失** 模块包括：`apis/aigc_api`、`drivers/milvus_driver`、`repos/knowledge_graph_repo`、`services/email`、`services/crawler/webpage_content_crawler`、`middleware/host_validation_middleware`、`views/*`、`atlas_repl/*`、`services/result_service`（安全相关分支）等。
- 评审方法：在 `common/tests/` 下按 **模块/关键词文件名** 抽样检索，**未见** 针对上述路径的专用测试文件或明显命中用例（与 §6 表述一致）。**不排除** 业务仓库其它 app 的集成测试间接覆盖部分行为。

### 各子域摘要

| 子域 | 说明 |
|------|------|
| **`AigcAPI` / `aigc_api`** | 出站 HTTP + settings；缺 dedicated 单测时，回归依赖手工或上层 `app_aibroker`。**质量风险**：契约变更难以及时发现。 |
| **驱动 `milvus_driver`、`repos/knowledge_graph_repo`** | 依赖外部服务/图查询构造；适合 **mock 驱动** 或容器集成测试。缺测时 **Cypher/注入与边界**（见 `REVIEW_common.md` §5.4）难以门禁。 |
| **`services/email`、`crawler/webpage_content_crawler`** | I/O 与 URL 策略；缺测时易与 P0 SSRF/超时类问题 **重复踩坑**。 |
| **`middleware/host_validation_middleware`、`views/*`** | Django/DRF 边界；Host 归一化、开放视图假设等在 **P0/P1 文** 已评，此处仅强调 **单测仍薄**（P3-17 与 `TODO` 一致）。 |
| **`atlas_repl/*`** | 解析与权限；缺测时 **畸形输入与注入面** 回归成本高。 |
| **`services/result_service`** | 索引与分发；与 P0「信任边界」相关用例若在 `common/tests` 缺席，则 **安全分支** 仍靠人工审查。 |

### 结论

**待改进**（按业务优先级 **分批** 补 **单元/契约测试** 或明确由 **哪一层** 集成测试承接）。与 `TODO.md` P3-17、P3-18 一致：不要求一次补全，但应在路线图或门禁中 **可追踪**。

---

## 4. 总览

| P3 项 | 结论 |
|-------|------|
| `generic_code_for_ret` | **待改进**（启发式 + i18n + 缺 common 侧单测） |
| `Singleton` 使用 | **通过**（实现与基础测例）；策略上 **待改进**（增量收敛与生命周期意识） |
| 缺测模块补全 | **待改进**（§6 所列区域仍偏薄，依业务优先级推进） |
