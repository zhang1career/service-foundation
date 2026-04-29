# 数据库索引优化建议（对照 `sf.sql` 与 API 查询）

本文档依据 `docs/schema/sf.sql` 中的表与索引定义，结合本仓库各 `app_*` 在 HTTP API 路径上触发的 ORM 查询（`repos/`、`services/`、`adapters/`）整理。**若 ORM 字段名与 SQL 列名不一致，以下以 Django 模型名为准，并注明物理列名。**

说明：

- **已有且基本匹配**的索引（如主键、`access_key` 唯一键、外键常见配套索引）不重复列出。
- 建议在生产环境用 `EXPLAIN` 对关键路径验证；复合索引列顺序需与**等值条件在前、范围/排序在后**的习惯一致。
- MySQL 5.7 不支持真正的 `DESC` 索引声明；以下“按时间倒序”类需求通常用 `(ct)` 或 `(ct, id)` 正序索引即可由优化器反向扫描或配合 `ORDER BY`。

---

## sf_know

### `knowledge`（模型 `KnowledgePoint`，表 `knowledge`）

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_know/repos/knowledge_point_repo.py`：`list_by_batch`、`get_ids_by_batch`、`delete_by_batch` | `WHERE batch_id = ? [AND stage=? AND status=?] ORDER BY seq` | 仅有 `idx_src(ut)` 及图/向量相关单列索引，**无 `batch_id`** | **`INDEX idx_knowledge_batch_seq (batch_id, seq)`**；若经常使用 `stage`/`status` 与 batch 组合筛选，可考虑 **`(batch_id, stage, status, seq)`**（需结合实际选择性评估）。 |
| 同上：`list_distinct_batch_ids` | `GROUP BY batch_id` + `MAX(ut)` + `ORDER BY max_ut DESC` | 同上 | **`batch_id` 单列或 `(batch_id, ut)`** 可减轻分组/聚合时的扫描代价。 |
| `list_knowledge_points`（无 `batch_id`） | `ORDER BY ct DESC` | `idx_src(ut)` 与排序列不一致 | 若该类列表 API 负载高：考虑 **`INDEX (ct)` 或 `(ct, id)`**。 |

### `batch`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_know/repos/batch_repo.py`：列表分页 | `ORDER BY ct DESC` | `sf.sql` 为 **`KEY idx_src (ut)`**，与排序列 **`ct` 不一致** | **`INDEX (ct)` 或 `(ct, id)`**，与代码一致；若历史数据仍以 `ut` 为主排序，应二选一并统一代码/SQL。 |

### `insight`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_know/repos/insight_repo.py`：`list_insights` | 可选 `perspective`、`type`、`status` + **`ORDER BY ut DESC`** | 仅有 `idx_src(ut)` | 单列 `ut` 可支撑纯时间序；若在生产中出现 **filtered + ORDER BY ut** 慢查询，可增加 **`(perspective, type, status, ut)`** 中与筛选条件匹配的左前缀索引（任选实际常用维度组合）。 |

---

## sf_cdn

### `d`（Distribution）

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_cdn/repos/distribution_repo.py`：`list_distributions` | **`ORDER BY ct`**，分页 `WHERE ct > ?`（marker） | 表上无 `ct` 相关二级索引（仅主键） | **`INDEX (ct)` 或 `(ct, id)`**，避免列表全表扫描。 |

### `invalid`（Invalidation）

---

## sf_user

### `token`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_user/repos/token_repo.py`：`deprecate_all_tokens_for_user` | `WHERE user_id = ? AND status = ?` | 已有 **`idx_user_token_status (user_id, status)`** | 一般已覆盖，**可保持**。 |

### `event`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `cancel_pending_events_by_notice`、`get_latest_pending_event_by_notice` | `biz_type`、`status`、`notice_channel`、`notice_target`（多处等值） | `idx_event_biz_status_notice_ct (biz_type, status, notice_target, ct)` **缺少 `notice_channel`** | 增加 **`(biz_type, status, notice_channel, notice_target, id)`** 或与现有索引合并重构，使 **`notice_channel` 出现在等值条件可用的前缀中**；`get_latest_pending_event_by_notice` 使用 **`ORDER BY id DESC`**，可将 **`id` 放在索引末尾**辅助排序。 |
| `get_latest_incomplete_event_by_notice` | `biz_type`、`status IN (...)`、`notice_target` + **`ORDER BY ct DESC`** | 同上，`status IN` 不利于长复合索引 | 视数据量可保留现状；若慢，可拆业务或增加覆盖 **`(notice_target, biz_type, ct)`** 等窄索引并配合 `EXPLAIN` 验证。 |
| `list_events` | 全表 **`ORDER BY ct DESC` 分页** | 无 `ct` 索引 | **`INDEX (ct)` 或 `(ct, id)`**。 |

---

## sf_snowflake

### `event`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_snowflake/repos/event_repo.py`：`list_event` | **`WHERE dcid = ? AND mid = ? ORDER BY ct DESC LIMIT ?`** | `idx_dc_mac (dcid, mid, event_type)`：查询**未使用 `event_type`**，排序键为 **`ct`** | **`INDEX (dcid, mid, ct)`**，使过滤与排序同序；若仍按 `event_type` 统计，可保留原索引或合并为 **`(dcid, mid, event_type, ct)`**（按查询二选一或并存）。 |

---

## sf_ai

### `call_log`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_aibroker/repos/call_log_repo.py`、metrics | **`ORDER BY ct DESC, id DESC`**；可选 `reg_id` | 仅 **`idx_ai_log_reg (reg_id)`** | 管理/查询接口在数据量大时易全表排序：建议 **`INDEX (ct, id)`**；若按租户：`**(reg_id, ct, id)****。 |

### `ai_job` / `ai_model`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_aibroker/repos/model_repo.py` | `WHERE provider_id = ? ORDER BY id DESC` | **`idx_ai_model_provider (provider_id, status)`** | 若常见过滤不含 `status`，优化器可能仅用 `provider_id`；若仍慢，可加 **`(provider_id, id)`** 或确认查询是否应带 `status`。 |

---

## sf_searchrec

### `doc_term`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_searchrec/adapters/index_store.py`：`search` | **`WHERE rid = ? AND term IN (...)`** | **`idx_search_doc_term_term (term)`**；唯一键 **`(rid, doc_key, term)`** | 检索以 **`rid` + `term`** 同时过滤为主，建议增加 **`INDEX (rid, term)`**（或 **`(rid, term, doc_key)`** 覆盖 `values()` 所需列），减少先按 `term` 再回表过滤 `rid` 的开销。 |
| `upsert_documents` | `DELETE WHERE rid = ? AND doc_key = ?` | 唯一约束可支持 | 已覆盖。 |

### `doc`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `index_store`：`filter(rid_id=rid, doc_key__in=...)` | 等值 + IN | **`UNIQUE (rid, doc_key)`** | 已覆盖。 |

---

## sf_saga

### `instance`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_saga/services/scan_service.py` | `status IN (...)` AND `next_retry_at <= ?` **`ORDER BY next_retry_at`** | **`idx_saga_instance_status_retry (status, next_retry_at)`** | 与查询一致，**一般足够**（`IN` 可能多段扫描）。 |
| `app_console/services/saga_console_query.py`：`list_instances` | **可选 `status = ?`** + **`ORDER BY id DESC` 分页** | 单独 `status` 与 `idx_saga_instance_flow` 等 | 若控制台在大量数据下按状态筛选慢：考虑 **`INDEX (status, id)`**。 |

### `flow_step`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_saga/services/saga_coordinator.py`：`_flow_has_need_confirm_step` | `WHERE fid = ? AND is_need_confirm = 1` | **`UNIQUE (fid, step_index)`** | 若 `EXISTS` 频繁且行数多，可选 **`INDEX (fid, is_need_confirm)`**（低优先级）。 |

---

## sf_tcc

### `branch_meta`

### `biz_meta` / `tx` / `tx_branch`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `list_biz_for_participant` | `WHERE rid = ? ORDER BY id` | **`idx_tcc_biz_reg (rid)`** | 通常可用；若极宽表可验证 **`(rid, id)`**。 |
| `scan_service` | `tx` 上 `status` + `next_retry_at` / `await_confirm_deadline_at` | 已有对应复合索引 | **已对齐**。 |

---

## sf_verify

### `verify_code`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_verify/repos/verify_code_repo.py`：`list_verify_codes_page` | **`ORDER BY ct DESC, id DESC` 分页** | `idx_verify_reg_ref`、`idx_verify_exp`，**无 `(ct, id)`** | **`INDEX (ct, id)`** 减轻后台列表排序/翻页成本。 |

---

## sf_notice

### `notice`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_notice/repos/notice_repo.py`：`list_notice_records_page` | **`ORDER BY ct DESC, id DESC`** | 已有 **`idx_notice_channel_status_ct`** 等，**无纯时间序列表索引** | 若列表为全量按时间倒序：建议 **`INDEX (ct, id)`**（与 channel/status 维度的索引互补）。 |

---

## sf_oss

### `m`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_oss/models/metadata.py` | `WHERE bucket_name = ? AND object_key = ?` | **`UNIQUE (bucket_name, object_key)`** | **已覆盖**；`idx_object_key(object_key)` 用于非 bucket 限定场景，保留即可。 |

---

## sf_config

### `config_entry`

| 查询来源 | 模式 | 现状 | 建议 |
|----------|------|------|------|
| `app_config/repos/config_entry_repo.py`：`list_entries_for_rid_and_key` | `WHERE rid = ? AND config_key = ? ORDER BY ut, id` | **`idx_config_config_key (rid, config_key)`** | **已覆盖**排序所需左前缀。 |

---

## 修订与落地

1. 在测试库执行 `EXPLAIN` 对比 **rows / Extra（Using filesort、Using where）**。
2. 新增索引建议在低峰期在线 `ALGORITHM=INPLACE, LOCK=NONE`（大表需评估）。
3. 若 Django `managed = False` 表与 `sf.sql` 长期手工维护，请将最终 DDL 同步回 `docs/schema/` 或团队约定的迁移流程，避免环境漂移。

---

*生成说明：基于仓库内 `*.py` 数据库访问与 `docs/schema/sf.sql` 对照；未包含仅单元测试使用的查询或已废弃路径。*
