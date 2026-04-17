# `common` P0 安全评审（对齐 `docs/plan/REVIEW_common.md` 第 7 节）

本文档仅覆盖计划第 **7** 节 **「P0 安全」** 所列范围：

1. 出站 URL / 重定向  
2. 敏感日志  
3. `HostValidationMiddleware`  
4. `result_service` / `distributed_tasks` 信任边界  

评价维度与 `REVIEW_common.md` 第 **2** 节一致：完善度、独立性、边界清晰度、性能关注点、安全关注点；结论用语：**通过 / 待改进 / 阻塞**。

---

## 1. 出站 URL 与重定向（`services/http/executor.py`、`services/http/client.py`）

### 现状摘要

- `request_sync` / `request_async` 将调用方传入的 `url` **原样**交给 `httpx.Client.request`，**未**在 `common` 层做 scheme、主机、解析后地址（含内网/元数据）等校验。与 `common/docs/TODO.md` **P0-1、P0-2** 所列「单一策略入口、拒绝 SSRF 常见目标」**尚未对齐**。  
- `httpx.Client()` 未显式传入 `follow_redirects`；当前依赖 **httpx 默认**（本环境 `httpx` 0.28.x 中 Client 层对重定向的默认策略为不自动跟随，与「需文档化并与产品策略一致」相比仍属**隐式依赖库版本**）。`executor` 的 `client.request(...)` 亦未传入 `follow_redirects`，行为由 Client 默认决定。  
- `utils/url_util.check_url` 仅判断「是否像含 scheme+netloc 的 URI」，**不承担** SSRF 防护，与 HTTP 层策略**未形成闭环**（与计划 **5.1 / 5.7** 中「URL 校验与 HTTP 层策略不重复、不冲突」尚需在实现落地后复核）。

### 维度简评

| 维度 | 说明 |
|------|------|
| 完善度 | 契约上未定义「允许的 URL 集合」；失败路径无「策略拒绝」类分型（与 TODO P2-10 相关但非本 P0 文范围）。 |
| 独立性 | 策略若以后集中在 settings/策略对象，可测性会提升；当前为「库默认 + 无校验」。 |
| 边界 | 符合「传输原语在 common」：但 **安全策略**应在何处实现（单一入口）仍缺文档与代码。 |
| 性能 | 无额外校验，热路径开销低；与 P0 安全目标无关。 |
| 安全 | **阻塞级缺口**：任意可调用 `request_sync` 的上游若传入内网 URL，存在经典 SSRF；重定向策略未在应用侧显式固定，升级 `httpx` 时需回归。 |

### 结论

**阻塞**（在未实现 TODO P0-1 / P0-2 所述策略前，不应视为 P0 安全项已闭合）。

---

## 2. 敏感日志（`services/http/executor.py`）

### 现状摘要

- 成功/失败路径均使用 `logger.info` / `logger.warning`，字段包含 **完整 `url=%s`**，即 **query / fragment 未剥离**（示例见 `executor` 中 `[http_call] ... url=%s`）。  
- 未对 `headers`、`params`、`json_body` 做脱敏；虽非直接写入日志，但若后续有人在同路径增加「调试打印」，仍缺成文约束。与 `common/docs/TODO.md` **P0-4** 一致：**未满足**。  
- `request_async` 同样记录完整 `url`。  
- `distributed_tasks.sync_call_task` 的日志含 `sync_fn_ref`、耗时、`task_id`，**未**记录 URL（HTTP 路径由 `request_sync` 侧记录），相对可控。

### 维度简评

| 维度 | 说明 |
|------|------|
| 完善度 | 缺少「生产默认可记录字段」与「禁止记录」清单的工程实现。 |
| 安全 | **待改进**：查询串常含 token、签名、PII；完整 URL 入 info/warning 不符合常见合规基线。 |

### 结论

**待改进**（与 TODO P0-4 对齐后方可标为通过）。

---

## 3. `HostValidationMiddleware`（`middleware/host_validation_middleware.py`）

### 现状摘要

- 用途：在 **Docker 等非标准 hostname**（无点号、非 IP、非 localhost）且 **`ALLOWED_HOSTS` 含 `*'`** 时，将 `HTTP_HOST` 规范为 `localhost[:port]`，以满足 RFC 与 `SecurityMiddleware` 顺序前提（见模块 docstring）。  
- **未**实现计划 **5.6** 中「拒绝错误 Host」的主动校验逻辑本身——该类校验仍依赖 Django `SecurityMiddleware` + `ALLOWED_HOSTS`；本中间件是 **归一化** 而非 **替代 allowlist**。  
- `common/docs/TODO.md` **P0-5** 指出：**缺单元测试**（含 `ALLOWED_HOSTS`、端口、`SERVER_NAME` 分支）。仓库内 `common/tests/` 抽样检索**未见**针对该中间件的测试，与计划 **第 6 节**「覆盖薄」一致。

### 维度简评

| 维度 | 说明 |
|------|------|
| 完善度 | 行为依赖 `ALLOWED_HOSTS == ['*']` 的分支较窄；边界（IPv6、国际化域名、畸形 Host）未在代码或测试中体现。 |
| 边界 | 职责清晰：仅处理「无点 hostname + 通配 allow」的归一化。 |
| 安全 | **待改进**：`ALLOWED_HOSTS='*'` 本身即弱化 Host 校验，中间件不加剧该点，但团队需在部署文档中明确「仅可信网络 / 前置网关校验 Host」等产品假设；**缺测**导致回归风险。 |

### 结论

**待改进**（功能与 P0「Host 相关」相关，但**测试缺口**使评审不能标为通过）。

---

## 4. `result_service` 信任边界（`services/result_service.py`）

### 现状摘要

- `get_result(result_index)` 从字典读取 `m`（模块名）、`f`（函数名）、`p`（参数 JSON 字符串），执行 `import_module(module_name)` 与 `getattr(module, func_name)`，再 `func(param_map)`。  
- **若 `result_index` 来自不可信输入**，则等效于 **服务端任意可导入模块上的可调用对象调用**，属于 **极高风险 RCE/越权** 面。`build_result_index` 从 `RESULT_INDEX_MAP` 取模块/函数名，**信任假设**是：`result_id` 与 `param_map` 仅来自服务端可信路径，且 **`get_result` 的入参绝不直接采用客户端构造的 `m`/`f`**。  
- 代码层**没有**白名单、`result_index` 签名校验或「仅允许自 `build_result_index` 产出格式」的校验；与 TODO **P0-3**「必要时加白名单或签名校验」**未对齐**。  
- 异常路径 `logger.exception(e)` 且向调用方返回 `repr(e)`，可能 **泄露内部异常细节**（与 P0 交叉的安全面，计划 **5.8** 亦有涉及）。

### 备注（仓库状态）

- 源码依赖 `common.consts.result_const.RESULT_INDEX_MAP`；若某检出环境中该常量模块缺失，属于**构建/发布**问题，不影响上述对 **信任模型** 的结论：`get_result` 的契约仍完全由入参字典决定。

### 维度简评

| 维度 | 说明 |
|------|------|
| 边界 | `RESULT_INDEX_MAP` 将「业务 result_id → 模块/函数」固定在服务端表侧；**边界清晰的前提是** 所有入口走 `build_result_index` 且索引不可被客户端篡改。 |
| 安全 | **阻塞**：缺少对 `result_index` 来源的**代码级**强制（白名单/签名/HMAC）。 |

### 结论

**阻塞**（直至信任边界以代码或统一网关约束落实，并补 **5.3** 建议用例方向中的安全测试）。

---

## 5. `distributed_tasks` 信任边界（`services/task/distributed_tasks.py`）

### 现状摘要

- `sync_call_task(sync_fn_ref, fn_kwargs)` 通过 `_import_callable(sync_fn_ref)` 解析 **任意** `module:qualname`，**无**允许列表；与 Celery「任务消息来自 broker」模型一致时，**信任边界在 broker 与 worker 准入**，而非本函数内部。  
- 与 HTTP 封装路径：`request_async` **固定** `SYNC_HTTP_REQUEST_FN_REF` 指向 `request_sync`，该路径下 `sync_fn_ref` **不可**由 HTTP 客户端直接注入。  
- **任意**调用 `sync_call_task.apply_async(..., sync_fn_ref="os:system", ...)` 的代码（或 broker 被攻破后伪造消息）仍可执行 **任意可导入可调用对象**，与 `result_service` 类似，属 **平台级信任假设**，需在架构文档中写清：**谁有权投递任务、broker 是否 TLS/鉴权**。  
- `_import_callable` 已有格式校验（单冒号）、非 callable 拒绝；**没有**模块路径白名单（TODO 与 **5.3** 中「策略落地后」一致）。  
- `_result_to_dict` 对类 `httpx.Response` 结果序列化 `headers`、`text`、`url`，若经 Celery 结果后端存储或回传，需与 **敏感数据** 策略一致（略超出本节「P0」但属安全相关）。

### 维度简评

| 维度 | 说明 |
|------|------|
| 完善度 | 对「公开 HTTP → Celery」的默认路径，与 `executor` 绑定后较清晰；泛化任务入口未收紧。 |
| 安全 | **待改进**：依赖部署与调用方自律；若产品要求「防误用/防伪造任务」，需白名单或签名校验（与 TODO 5.3 一致）。 |

### 结论

**待改进**（在明确「仅内部任务生产者」前提下可接受；若暴露面更大则需升至 **阻塞** 并落地白名单）。

---

## 6. P0 安全总表（执行顺序 1 的对照）

| 主题 | 计划 / TODO 参照 | 当前结论 |
|------|------------------|----------|
| 出站 URL / SSRF / scheme | TODO P0-1、P0-2；计划 5.1 | **阻塞** |
| 重定向策略显式化 | TODO P0-2 | **待改进**（依赖 httpx 默认，未文档化） |
| 敏感日志 | TODO P0-4；计划 5.1 | **待改进** |
| `HostValidationMiddleware` | TODO P0-5；计划 5.6 | **待改进**（缺测 + 部署假设需书面化） |
| `result_service` 动态调用 | TODO P0-3；计划 5.3 | **阻塞** |
| `distributed_tasks` 动态加载 | 计划 5.3、第 7 节 | **待改进**（视暴露面可升级为阻塞） |

---

## 7. 建议的后续动作（仅列与本节评价直接相关的）

1. 实现并单测：**出站 URL 策略**（单入口）、**日志脱敏/字段清单**（与 `executor` 对齐）。  
2. 为 **`HostValidationMiddleware`** 补 `common/tests/` 用例（覆盖 TODO P0-5 所列分支）。  
3. 为 **`get_result`** 增加 **不可信输入不可达** 的硬约束（白名单或签名），并补充 **5.3** 方向的测试。  
4. 评估 **`sync_call_task`** 的调用面：若仅内部固定 `sync_fn_ref`，文档化即可；否则加 **模块:符号** 白名单或任务签名。

以上与 `REVIEW_common.md` **第 2 节维度**及 **第 5 节** 各子域测试建议一致，不展开 P1/P2/P3 项。
