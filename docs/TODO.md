# TODO

与 `docs/insert.sql` 中真实库结构对照后，迁移状态（`0001_initial` 的 `SeparateDatabaseAndState`）与模型仍存在的偏差与可选改进项如下。执行 `migrate` 当前不会对已有业务表做 DDL；下列项用于缩小 **ORM/迁移状态** 与 **MySQL** 的差异，降低日后 `makemigrations` 噪音并避免误以为库里已有某些索引或约束。

---

##环境与库名

- **AI 库名**：dump 为 `sf_ai`，`settings` 默认可能为 `sf_aibroker`（以 `.env` 为准）。若团队以 dump 为准，需统一环境变量与文档。

---

## `sf_know` / `app_know`

- **`insight`**：`insert.sql` 中 `perspective` / `type` / `status` 为 `NOT NULL DEFAULT 0`；模型上 `perspective` 仍为可空，与库不完全一致。可按需收紧为不可空并设默认 `0`。
- **`insight` 索引**：库仅有 `idx_src (ut)`；模型在 `type` / `status` / `perspective` 上声明了 `db_index`，迁移状态中比库多索引。若不以这些列为查询条件，可去掉多余 `db_index`或改为显式 `Meta.indexes` 与库一致。
- **`batch` 索引**：库仅有 `idx_src (ut)`；模型对 `source_type`、`ct`、`ut` 等声明了 `db_index`，状态多于库。同上处理。
- **`knowledge`**：库中大量列为 `NOT NULL` 与 `varchar(512)` 等默认值；模型多为可空 + `TextField`，与库可空性/类型不完全一致。若要以库为权威，需逐列对齐并更新迁移状态（改动面大）。
- **`knowledge` 索引**：库为 `idx_src(ut)`、`idx_graph_sub`、`idx_graph_obj`、`idx_vec_sub`、`idx_vec_obj`、`idx_graph_brief`；当前迁移状态使用 Django 生成的 `knowledge_*` 索引名与不同列组合。可对齐名称与字段列表。

---

## `sf_searchrec` / `app_searchrec`

- **`doc` 唯一约束名**：库为 `uni_search_doc_doc`；模型/迁移为 `uniq_searchrec_doc_rid_key`。可二选一统一（改模型约束名或接受差异）。
- **`doc` 二级索引**：库无单独 `rid` 索引；状态中有 `idx_searchrec_doc_rid`。若库不打算加该索引，应从模型/状态中移除以免误导。
- **`doc` CHECK 约束**：模型声明了 `CheckConstraint`，`insert.sql` 中无。若库不建 CHECK，可保留仅应用层校验，或从 `Meta.constraints` 与迁移状态中移除。
- **`doc_term` 索引**：库为 `idx_search_doc_term_term (term)`；状态为 `idx_doc_term_rid_term (rid, term)`。按实际查询对齐。
- **`event`**：库索引名为 `idx_search_event_type`，列为 `(rid, event_type, ct)`；状态为 `idx_event_rid_type_ct`。库中 `uid` / `did` 非空带默认，模型为可空。按契约对齐名称、可空性与默认值。
- **`reg`**：库仅有 `UNIQUE uni_search_reg_access_key`；状态另有 `name`、`status` 索引。若库不加索引，应从模型中移除对应 `Meta.indexes`。

---

## `sf_user` / `app_user`

- **`event` 复合索引**：库为 `idx_event_biz_status_notice_ct (biz_type, status, notice_target, ct)`；模型与迁移为 `(biz_type, status, ct)`，缺少 `notice_target`。建议补上该列以匹配库与查询计划。
- **`event` 单列索引名**：库为 `idx_event_verify_code_id`；Django 迁移中可能为截断后的自动名（如 `event_verify__082e0c_idx`）。可在 `Meta.indexes` 中显式 `name=` 与库一致。
- **`token` 复合索引名**：库为 `idx_user_token_status`；迁移中为 `token_user_id_6487e2_idx`。可显式命名对齐。
- **`user`**：库仅三个 UNIQUE（`uni_user_email` / `uni_user_phone` / `uni_user_name`），无 `status`、`ct` 二级索引；模型 `Meta.indexes` 含 `status`、`ct`。若库不建这些索引，应移除或改为与库一致。

---

## `sf_verify` / `app_verify`

- **`reg` 唯一约束名**：库为 `uni_verify_reg_access_key`；模型为 `verify_reg_access_key_uniq`。可统一命名。
- **`reg` 额外索引**：库无 `name` / `status` / `ct` / `ut` 二级索引；模型声明了多项。按库删减或按需在库上 `ALTER` 补齐。
- **`verify_code` 索引**：库为 `idx_verify_exp (expires_at)`、`idx_verify_reg_ref (reg_id, ref_id)`；与当前模型/迁移中的索引定义不同。按实际查询对齐。
- **`verify_log` 索引**：库为 `idx_verify_log_code (code_id)`、`idx_verify_log_reg_ref (reg_id, ref_id)`；当前状态为 `(reg_id, ct)`、`(code_id, ct)`。按库对齐列与名称。
- **`verify_log` 存储引擎与主键**：库为 `MyISAM`，`id` 为有符号 `bigint`；模型为 `BigAutoField`。若需与库完全一致，需评估是否改表引擎/类型（通常仅文档说明即可）。

---

## `sf_cms` / `app_cms`

- **`content_meta`**：dump 中存在遗留列 `Column 4`（text），Django 未建模。可在库中 `DROP COLUMN` 或单独文档说明忽略。
- **`content_meta` 唯一键名**：库为 `uni_cms_content_meta_name`；`unique=True` 可能生成不同约束名。可在 `Meta.constraints` 中显式命名与库一致。

---

## `sf_cdn` / `app_cdn`

- **`d` / `invalid`**：库中无 `status` 等字段上的二级索引；模型对部分字段使用了 `db_index=True`，仅存在于迁移状态。若与库严格一致，可去掉多余 `db_index`。

---

## `sf_ai` / `app_aibroker`

- **`ai_model.param_specs`**：库为 `varchar(1024)`；模型为 `TextField`，语义足够，一般无需改。若需与 DDL 完全一致可改为 `CharField(max_length=1024)`（注意超长内容风险）。
- **字段默认值**：如 `ai_job.reg_id`等在库中有 `DEFAULT 0`，模型部分字段无默认；属轻微差异，按需统一。

---

## 新环境 / 空库

- 当前各业务 `0001_initial` 使用 `SeparateDatabaseAndState` 且 `database_operations=[]`，**不会在空库中建表**。新环境需先执行与 `insert.sql` 等价的结构导入，或另增会真正执行 DDL 的迁移/脚本。
