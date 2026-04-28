# app_tcc 待办（按重要程度）

来源：`tcc设计评审_bd0b3152.plan.md`（本地 Cursor 计划；执行顺序与依赖已合并为优先级）。

---

## P0 — 阻塞运行与数据正确性

1. **工程对接**：`INSTALLED_APPS`、`DATABASES["tcc_rw"]`、`DATABASE_ROUTERS` 接入 `app_tcc.db_routers.ReadWriteRouter`；`urls` 在 `APP_TCC_ENABLED` 下挂载 `api/tcc/`（与仓库惯例一致）。
2. **模型与迁移**：全局事务、分支、参与者注册三表字段与计划对齐（雪花 `global_tx_id`、分支 `branch_index`、幂等键、HTTP 摘要字段、阶段/截止时间/重试/人工介入字段等）；**索引**：`(status, next_retry_at)`、全局事务 id、分支 `(global_tx_id, branch_index)`。
3. **乐观锁推进**：扫描与协调路径对「抢到执行权」统一采用 **`UPDATE ... WHERE id = ? AND version = ?`**（更新成功才算 claim）。
4. **配置**：`.env` / `settings` 读取 `DB_TCC_*`（默认库名 `sf_tcc`）；全局阶段超时、`TCC_MAX_AUTO_RETRIES`、出站 HTTP 超时等（首版不设 per-participant 超时）。

---

## P1 — 协调核心（Try / Confirm / Cancel 语义）

5. **幂等键**：全局事务 `idem_key` 由请求头 **`X-Request-Id`**（int64）提供，与 Saga 一致。
6. **参与者 HTTP**：封装 Try / Confirm / Cancel 出站调用；分支记录回调 URL/path、幂等键、**截断**的 `last_http_status` / `last_error`。
7. **协调器**：按 `branch_index` **顺序 Try**；多分支时 **Confirm 与 Try 顺序相反**；**Cancel仅对已 Try 成功的分支**，顺序与 Try 相反；Try 失败进入 Cancel 路径。
8. **失败归宿**：重试超限或不可恢复错误 → **`NEEDS_MANUAL`**，写入 `manual_reason` + 简要快照（阶段、各分支最后 HTTP 状态/截断信息、重试次数等）。

---

## P2 — HTTP API与内网鉴权

9. **基础鉴权**：注册与协调 API 保留**共享密钥**（如 `TCC_INTERNAL_API_KEY`）或等价约束，与「不设 URL 白名单」并存；若产品明确「完全依赖网络隔离」，再移除鉴权相关实现与文档表述。
10. **注册 API**：创建/更新参与者及三阶段回调配置（**仅 app_console / 内网调用方**）。
11. **事务 API**：开事务 +顺序 Try；对外 Confirm / Cancel；按 `global_tx_id` **查询**状态与分支摘要。

---

## P3 — 周期扫描（兜底重试）

12. **`manage.py tcc_scan`**（或等价）：查询 **`WHERE status IN (...) AND next_retry_at <= now() ORDER BY next_retry_at LIMIT N`**；依赖 P0 的 version乐观锁 claim；**不依赖** `SKIP LOCKED`。
13. **调度**：django_crontab 或外部 scheduler 接入（与运维约定）。

---

## P4 — 测试与交付说明

14. **单测**：Mock 参与者 HTTP；覆盖：Try 全成功 → **逆序 Confirm**；Try 中途失败 → **仅已成功分支逆序 Cancel**；扫描重试与**并发 claim**。
15. **环境与运维说明**：`.env.example` / 部署说明中补齐 TCC 相关变量与扫描任务（不写冗长文档，保持可执行清单即可）。

---

## 明确不在首版范围（备忘）

- Per-participant 超时字段或配置中心对接。  
- 独立控制台 UI、完整告警流水线、Redis 分布式锁。  
- 对外强制 HTTPS、签名校验、host 白名单（内网首版；与 P2 基础鉴权不矛盾）。
