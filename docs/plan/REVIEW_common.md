# `common` 包评价计划

本文档用于**结构化评审**仓库内 `common/` 共享层：列出可评价单元、统一打分维度，并给出**可落地的测试用例方向**（可与 `common/tests/` 及业务侧集成测试配合）。实施细节与已知风险另见 `common/docs/TODO.md`。

---

## 1. 范围与约定

- **范围**：`common/` 下全部 Python 源码（不含 `common/tests/`），含 `consts`、`enums`、`exceptions`、`utils`、`services`、`drivers`、`middleware`、`views`、`repos`、`apis`、`annotations` 等。
- **功能单元**：以**模块内顶层** `class` / `def` / `async def` 为主（私有实现 `_xxx` 随所属公开单元一并评审）；`consts/*.py` 以**命名常量集合**为单元；`dict_catalog/bundled.py` 为**导入副作用注册**，无独立符号。
- **评审输出**：对每个单元或子域填写：完善度、独立性、边界清晰度、性能关注点、安全关注点、在架构中的层级角色；结论用「通过 / 待改进 / 阻塞」等简短标注，并链到具体测试或 issue。

---

## 2. 评价维度（逐项检查）

| 维度 | 关注点 | 提示性问题 |
|------|--------|------------|
| **是否完善** | 契约、错误处理、边界输入、文档与命名一致性 | 空值、超大输入、非法格式、并发下行为是否定义清楚？失败时是否可诊断且不泄露内部？ |
| **是否独立** | 可测性、对 Django/settings/全局单例的耦合 | 能否在不启动全栈的情况下单测？是否被错误地绑到某一微服务域？ |
| **边界是否清晰** | 分层：纯工具 vs 出站传输 vs 驱动 vs 视图 | 是否把业务策略塞进 `common`？是否违反「仅微服务依赖 `common`，`common` 不依赖 `app_*`」？ |
| **性能** | 热路径、分配、连接池、批处理、O(n) 隐患 | 是否在循环内做 I/O？池是否泄漏？大列表/大 JSON 是否需流式或上限？ |
| **安全性** | SSRF、注入、敏感数据入日志、任意代码执行、开放端点 | URL/重定向/主机校验？动态 `import`/`getattr` 的信任源？JWT/密钥使用？ |

---

## 3. 在架构设计中的角色

建议将 `common` 内代码按**依赖方向**理解为下列层次（上层可依赖下层，反之禁止）：

```text
views / middleware          ← HTTP 边界、Django 集成
    ↓
services（http/storage/multimedia/task/…）  ← 可复用过程、出站 I/O
    ↓
repos / drivers             ← 特定存储与外部系统的薄封装
    ↓
utils / pojo / enums / consts / exceptions / annotations / components
```

- **与仓库规则对齐**：领域相关的出站 HTTP 契约（如绑定某一上游 API 的 client）宜在**拥有该 API 的应用**内；`common` 保留**通用原语**（如通用请求工具、与具体业务 ret 码无关的传输）——参见 `common/docs/TODO.md` 中 `AigcAPI` 等待迁项。
- **禁止**：`common` 内导入或调用 `app_*` 微服务包；测试亦同（参见已跳过用例 `common/tests/services/graph/test_sensitive_dfa_repo.py`）。

---

## 4. 功能单元清单（顶层符号）

以下由源码 AST 扫描生成（仅 `common/`，排除 `tests`）。**常量模块**（`common/consts/*.py`）主要为模块级常量，不单独逐函数列出，评审时以文件为单位检查命名、魔法数、重复与用途。

### 4.1 `annotations/`

| 模块 | 单元 |
|------|------|
| `cache.py` | `_args_key`, `django_cached`, `local_ttl_cached` |
| `http_client_cache.py` | `apply_http_client_cache_headers`, `_effective_max_age_seconds`, `http_response_client_cache` |
| `logger.py` | `timing` |
| `pd.py` | `check_input` |

### 4.2 `apis/`

| 模块 | 单元 |
|------|------|
| `aigc_api.py` | `AigcAPI` |

### 4.3 `atlas_repl/`

| 模块 | 单元 |
|------|------|
| `repl.py` | `get_mongo_uri`, `_to_json_safe`, `_extract_parens_args`, `_parse_find_args`, `_parse_method_chain`, `_extract_first_json`, `_split_two_json`, `_match_db_coll_method`, `_try_expand_shorthand`, `_default_state`, `repl_step` |

### 4.4 `cdn/`

| 模块 | 单元 |
|------|------|
| `protocol.py` | `CdnProviderProtocol` |

### 4.5 `components/`

| 模块 | 单元 |
|------|------|
| `singleton.py` | `_Singleton`, `Singleton` |

### 4.6 `dict_catalog/`

| 模块 | 单元 |
|------|------|
| `registry.py` | `register_dict_code`, `_ensure_bundled_common`, `_compute_dict_by_codes`, `get_dict_by_codes`, `warm_dict_catalog_bundled`, `dict_value_to_label`, `clear_dict_registry_for_tests` |
| `warmup.py` | `prime_http_dict_cache` |
| `bundled.py` | （导入副作用，无顶层符号） |

### 4.7 `drivers/`

| 模块 | 单元 |
|------|------|
| `milvus_driver.py` | `LocalMilvusDriver` |
| `mongo_driver.py` | `_build_vector_index_name`, `MongoDriver` |
| `neo4j_driver.py` | `Neo4jDriver` |

### 4.8 `enums/`

| 模块 | 单元 |
|------|------|
| `aigc_invoke_op_enum.py` | `AigcInvokeOp` |
| `app_enum.py` | `AppEnum` |
| `content_type_enum.py` | `ContentTypeEnum` |
| `nested_type_enum.py` | `NestedParamType`, `AibrokerNestedParamTypeDict` |
| `routine_stage_enum.py` | `RoutineStageEnum` |
| `service_reg_status_enum.py` | `ServiceRegStatus` |

### 4.9 `exceptions/`

| 模块 | 单元 |
|------|------|
| `base_exception.py` | `generic_code_for_ret`, `generic_message_for_ret`, `http_status_for_ret`, `CheckedException`, `UncheckedException` |
| `checked/invalid_argument_error.py` | `InvalidArgumentError` |
| `checked/invalid_model_response_error.py` | `InvalidModelResponseError` |
| `checked/object_storage_error.py` | `ObjectStorageError` |
| `checked/upstream_http_error.py` | `UpstreamHttpError` |
| `unchecked/configuration_error.py` | `ConfigurationError` |
| `unchecked/shell_command_error.py` | `ShellCommandError` |

### 4.10 `middleware/`

| 模块 | 单元 |
|------|------|
| `host_validation_middleware.py` | `HostValidationMiddleware` |

### 4.11 `pojo/`

| 模块 | 单元 |
|------|------|
| `form.py` | `UploadingFileForm` |
| `response.py` | `ResponseEmbeddedError`, `Response` |

### 4.12 `repos/`

| 模块 | 单元 |
|------|------|
| `knowledge_graph_repo.py` | `KnowledgeGraphRepo`, `build_props_str`, `build_props_cypher` |

### 4.13 `services/crawler/`

| 模块 | 单元 |
|------|------|
| `webpage_content_crawler.py` | `WebPageContentCrawler` |

### 4.14 `services/email/`

| 模块 | 单元 |
|------|------|
| `email_service.py` | `send_email`, `send_email_multipart`, `build_logo` |

### 4.15 `services/http/`

| 模块 | 单元 |
|------|------|
| `client.py` | `get_http_client`, `_resolve_limits`, `_resolve_timeout`, `close_all_http_clients` |
| `errors.py` | `HttpCallError` |
| `executor.py` | `request_sync`, `request_async`, `_queue_for_pool`, `_normalize_data` |
| `pools.py` | `HttpClientPool`, `pool_id` |

### 4.16 `services/multimedia/`

| 模块 | 单元 |
|------|------|
| `audio_service.py` | `df_to_voice`, `str_to_voice` |
| `gif_service.py` | `image_to_gif` |
| `image_service/decorative_image_service.py` | `plot_value_time_line`, `plot_daily_candlestick` |
| `image_service/simple_image_service.py` | `plot_value_time_line` |
| `video_service.py` | `audio_image_to_video_by_ffmpeg`, `build_command`, `_run_command`, `audio_gif_to_video` |

### 4.17 `services/storage/`、`services/task/`、`services/thread/`、`services/result_service.py`

| 模块 | 单元 |
|------|------|
| `storage/s3_service.py` | `get_s3_client`, `upload`, `download`, `download_obj`, `_generate_presigned_url`, `_build_ext_args` |
| `task/distributed_tasks.py` | `sync_call_task`, `_import_callable`, `_restore_payload_data`, `_result_to_dict` |
| `thread/thread_pool.py` | `get_thread_pool_executor`, `shutdown_thread_pool_executors`, `_atexit_shutdown` |
| `result_service.py` | `build_result_index`, `get_result` |

### 4.18 `utils/`（工具模块较多，按文件列出）

| 模块 | 单元 |
|------|------|
| `callback_verify.py` | `verify_callback` |
| `char_util.py` | `replace_char` |
| `date_util.py` | `get_now_timestamp`, `get_now_timestamp_ms`, `get_natual_range_of_date`, `get_date_int_of_data_str`, `get_timestamp_int_of_data_str`, `get_timestamp_int_of_datatime`, `get_datetime_of_date_str`, `get_datetime_of_timestamp`, `get_date_str_of_datetime`, `get_human_readable_date_str_of_datetime`, `get_date_int_of_timestamp`, `get_days_before` |
| `debug_util.py` | `dd` |
| `df_util.py` | `extract_column_and_combine`, `extract_row_and_combine`, `check_empty`, `df_of_dict_list` |
| `dict_coll_util.py` | `add_to_list`, `add_to_set`, `update_to_set`, `add_to_dict`, `add_to_dict_set`, `update_to_dict_set` |
| `dict_util.py` | `get_at_path`, `set_at_path`, `ensure_parent_for_path`, `_nested_path_keys`, `check_empty`, `get_first_key`, `get_key_list`, `get_value_list`, `dict_first_key`, `dict_first_value`, `dict_first_pair`, `get_multiple_value_list`, `get_multiple_value_dict`, `columns_copy`, `columns_copy_batch`, `get_by_dict`, `set_by_dict`, `del_by_dict`, `build_key_from_dict`, `merge`, `invert`, `dict_by`, `nest_clip`, `map_dict_values_by_shared_keys`, `sort_and_hash` |
| `django_db_router.py` | `AppLabelDatabaseRouter` |
| `django_util.py` | `schedule_on_commit`, `post_like_mapping_to_dict`, `effective_setting_str`, `post_to_dict` |
| `enum_util.py` | `enum_contains`, `enum_item_by_name` |
| `env_util.py` | `load_env` |
| `file_util.py` | `app_path` |
| `format_util.py` | `format_for_input`, `format_for_output`, `_format_price`, `_format_price_to_str`, `_format_profit`, `_format_profit_to_str`, `_format_coef`, `_format_coef_to_str` |
| `hash_util.py` | `md5` |
| `http_auth_util.py` | `build_auth_headers`, `authorization_header_from_request`, `parse_bearer_token` |
| `http_util.py` | `parse_http_target`, `normalize_http_path`, `http_origin_url`, `response_as_dict`, `post_payload`, `resolve_request_id`, `attach_request_id_header`, `response_with_request_id`, `with_type`, `resp_ok`, `resp_warn`, `resp_err`, `resp_exception`, `drf_unified_exception_handler`, `UnifiedExceptionMiddleware`, `_wants_json`, `get`, `post` |
| `json_util.py` | `json_encode`, `json_decode`, `json_decode_from_bytes` |
| `jwt_codec.py` | `encode_hs256_token`, `decode_hs256_token`, `claims_with_expiry` |
| `list_util.py` | `check_empty`, `list_first_element`, `column_of`, `field_of`, `index_by`, `cartesian_product`, `append_and_unique_list` |
| `map_util.py` | `qs_to_df`, `list_to_df`, `group_to_df_list`, `qs_to_dict_list`, `qs_to_dict_group`, `tuple_to_list` |
| `neo4j_util.py` | `extract_field` |
| `nested_typed_tree_util.py` | `try_parse_json_list`, `iter_typed_tree_leaves`, `walk_typed_tree_preorder`, `validate_typed_record_tree`, `coerce_to_bool`, `coerce_to_int_bounded`, `coerce_to_float_bounded`, `coerce_to_enum_choice`, `coerce_to_json_list`, `coerce_to_object_list`, `coerce_to_object_like`, `coerce_to_str_with_max_len`, `wrap_object_array_dict_branches_as_single_element_lists`, `apply_field_coercion` |
| `number_util.py` | `float_digit1`, `float_digit4`, `float_digit4_without_tailing_zeros` |
| `numpy_util.py` | `list_to_np_array` |
| `obj_util.py` | `prop_of`, `map_of` |
| `page_util.py` | `build_page`, `slice_window_for_page` |
| `qs_util.py` | `check_empty` |
| `redis_url_util.py` | `redis_location_with_db` |
| `serialize_util.py` | `dict_to_text` |
| `set_util.py` | `check_empty`, `diff` |
| `sql_util.py` | `build_mask_in_cond`, `raw_query`, `fetchall_to_list` |
| `stat_util.py` | `calculate_rising_rates` |
| `string_coll_util.py` | `sort_and_hash`, `column_of_first_char`, `index_by_first_char` |
| `string_util.py` | `check_blank`, `lowercase`, `explode`, `implode`, `wrap_with_quotes`, `wrap_with_quotes_batch`, `truncate`, `trim`, `multi_line_to_single_line`, `downcase_only_if_first_char_is_uppercase` |
| `text_util.py` | `get_first_paragraph`, `remove_appending` |
| `tls_util.py` | `check_version` |
| `tuple_util.py` | `append_and_unique_tuple` |
| `type_util.py` | `parse_int_or_default`, `as_list`, `as_dict` |
| `url_util.py` | `check_url`, `remove_url_param`, `extract_all`, `extract_domain`, `extract_sub_url`, `url_encode`, `url_decode` |

### 4.19 `views/`

| 模块 | 单元 |
|------|------|
| `atlas_repl_view.py` | `AtlasReplView` |
| `dict_codes_view.py` | `DictCodesView` |

### 4.20 `consts/`（按文件为单元）

`cache_const`, `http_const`, `image_const`, `list_const`, `number_const`, `prompt_const`, `query_const`, `response_const`, `s3_const`, `string_const`。

---

## 5. 分域评审要点与针对性测试用例

下列用例以 **`test_<场景>_<预期>`** 命名建议，便于在 `common/tests/` 或业务测试中落地；外部依赖一律 `unittest.mock` 或假实现。

### 5.1 出站 HTTP（`services/http/*`、`utils/http_util.py` 中与请求相关的部分）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| SSRF / URL 策略（完善度、安全） | `test_request_sync_rejects_disallowed_host`（内网 IP、元数据地址、非 http(s) scheme）；`test_redirect_policy_does_not_bypass_ssrf_check`（若开启重定向） |
| 超时与连接失败分型（边界、完善度） | `test_request_sync_maps_timeout_to_http_call_error`；`test_request_sync_connection_error_has_cause_chain` |
| 连接池与资源（性能、独立） | `test_close_all_http_clients_idempotent`；`test_pool_key_stable_for_same_config`（`pool_id` / `HttpClientPool`） |
| 敏感日志（安全） | `test_request_sync_logs_redact_authorization`（mock logger，断言无裸密钥）；`test_error_path_no_full_url_query_in_log`（与产品策略一致） |
| 默认与配置（独立、边界） | `test_resolve_timeout_single_default_layer`（避免多层 `or` 掩盖错误配置，与 `common/docs/TODO.md` P1-8 对齐） |

### 5.2 认证与 JWT（`utils/http_auth_util.py`、`utils/jwt_codec.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| Bearer 解析鲁棒性（完善） | `test_parse_bearer_token_rejects_malformed`；`test_authorization_header_case_insensitive_scheme`（已有类似可合并） |
| JWT 过期与签名（安全、完善） | `test_decode_hs256_token_rejects_expired`；`test_decode_hs256_token_rejects_bad_signature`；`test_encode_decode_roundtrip_claims` |
| 密钥不落日志（安全） | `test_build_auth_headers_never_logged_by_caller`（由调用方配合，或在文档中规定） |

### 5.3 动态加载与结果分发（`services/result_service.py`、`services/task/distributed_tasks.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 信任边界（安全） | `test_get_result_rejects_unknown_index`；`test_build_result_index_only_allows_server_side_map`（若引入白名单则测非法模块路径被拒绝） |
| Celery/序列化边界（完善） | `test_sync_call_task_payload_roundtrip`；`test_import_callable_rejects_non_whitelisted_module`（策略落地后） |

### 5.4 存储与驱动（`services/storage/s3_service.py`、`drivers/*`、`repos/knowledge_graph_repo.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 凭证与预签名 URL（安全） | `test_presigned_url_does_not_embed_secret_in_logs`；`test_upload_content_type_honored` |
| 驱动生命周期（性能、独立） | `test_mongo_driver_connect_lazy_or_idempotent`（按实际实现）；`test_neo4j_driver_close_releases_resources` |
| Repo Cypher 拼接（安全、完善） | `test_build_props_cypher_escapes_special_chars`（防注入）；空 props 行为 |

### 5.5 多媒体与爬虫（`services/multimedia/*`、`services/crawler/webpage_content_crawler.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 命令注入（安全） | `test_video_build_command_rejects_shell_metacharacters_in_paths`；ffmpeg 参数化测试 |
| 资源上限（性能、完善） | `test_audio_service_rejects_oversized_input`（若需上限）；大文件 mock |
| 爬虫 SSRF / 超时 | `test_crawler_respects_url_allowlist`；`test_crawler_timeout` |

### 5.6 Django 集成（`middleware/host_validation_middleware.py`、`views/*`、`utils/django_util.py`、`utils/django_db_router.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| Host 头攻击（安全） | `test_host_validation_allows_configured_hosts`；`test_host_validation_rejects_wrong_host`；端口、`ALLOWED_HOSTS` 边界（见 `common/docs/TODO.md` P0-5） |
| 开放端点（安全、架构） | `test_dict_codes_view_auth_assumption_documented`（若 `authentication_classes = []`，测速率限制/仅内网等产品假设） |
| `post_to_dict` 契约（边界） | `test_post_to_dict_requires_drf_request` 或重命名后的契约测试（P1-7） |

### 5.7 工具库（`utils/dict_util.py`、`nested_typed_tree_util.py`、`url_util.py` 等）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 路径穿越 / 深层合并（完善） | 已有边界测试可扩展：`test_dict_util_boundary_*`、`test_nested_typed_tree_invalid_shape` |
| URL 校验与 SSRF 辅助（安全） | `test_check_url_blocks_internal_network`（若 `check_url` 承担策略）；与 HTTP 层策略不重复、不冲突 |
| 纯函数性能（性能） | 对 `sort_and_hash`、`nest_clip` 等大结构用例做基准（可选，列入 perf 文档） |

### 5.8 异常与 API 响应（`exceptions/*`、`pojo/response.py`、`utils/http_util.py` 的 `resp_*`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 不向客户端泄露栈信息（安全） | `test_resp_err_masks_internal_message_in_production`（settings 切换） |
| `generic_code_for_ret` 启发式（完善） | `test_generic_code_for_ret_explicit_mapping_preferred`（与 P3-15 对齐） |

### 5.9 注解与缓存（`annotations/cache.py`、`annotations/http_client_cache.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 缓存键稳定性（正确性） | `test_django_cached_key_includes_relevant_args`；`test_http_client_cache_headers_respect_max_age`（部分已有） |

### 5.10 `AigcAPI` 与 `apis/aigc_api.py`（架构）

- 评审时单独跟踪：**归属是否应迁出 `common`**、配置与密钥管理、流式响应与超时。
- 测试建议：`test_aigc_api_uses_settings_single_source`；mock 上游；**迁出后**测试随应用包移动。

### 5.11 `atlas_repl`（`atlas_repl/repl.py`、`views/atlas_repl_view.py`）

| 评审重点 | 建议测试用例 |
|----------|----------------|
| 注入与权限（安全） | `test_repl_step_rejects_arbitrary_code`（若仅允许白名单命令）；视图鉴权 |
| 解析鲁棒性（完善） | `test_parse_find_args_various_quoting`；畸形输入不崩溃 |

---

## 6. 现有测试覆盖对照（抽样）

下列模块在 `common/tests/` 中**已有**对应测试（评审时优先复用/补强，而非从零写）：  
`annotations/cache`, `annotations/http_client_cache`, `components/singleton`, `drivers/mongo_driver`, `drivers/neo4j_driver`, `services/http/*`, `services/storage/s3_service`, `services/task/distributed_tasks`, `services/thread/thread_pool`, `services/multimedia` 多项, `utils/*` 大量, `test_dict_catalog`, `test_nested_type_enum`, `enums/test_enum`。

**覆盖薄或缺失**（与 `common/docs/TODO.md` P3-17 一致，计划优先补）：  
`apis/aigc_api`, `drivers/milvus_driver`, `repos/knowledge_graph_repo`, `services/email`, `services/crawler/webpage_content_crawler`, `middleware/host_validation_middleware`, `views/*`, `atlas_repl/*`, `services/result_service`（安全相关分支）。

---

## 7. 建议执行顺序

1. **P0 安全**：出站 URL/重定向、敏感日志、`HostValidationMiddleware`、`result_service` / `distributed_tasks` 信任边界。  
2. **P1 架构**：`AigcAPI` 归属、`DictCodesView` 假设、`django_util.post_to_dict` 契约。  
3. **P2 可观测与错误模型**：`HttpCallError` 分型、异常链、`request_sync` 可注入客户端（若立项）。  
4. **P3 质量**：`generic_code_for_ret`、Singleton 使用收敛、缺测模块按业务优先级补全。

---

## 8. 附录：更新清单方式

重新生成第 4 节顶层符号列表时，在仓库根目录执行：

```bash
python3 - <<'PY'
import ast
from pathlib import Path

def scan_file(p: Path):
    tree = ast.parse(p.read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.append(f"class {node.name}")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            pref = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
            out.append(pref + node.name)
    return out

root = Path("common")
for py in sorted(root.rglob("*.py")):
    if "/tests/" in str(py):
        continue
    syms = scan_file(py)
    if syms:
        print(f"### {py.relative_to(root)}\n" + "\n".join(f"  - {s}" for s in syms))
PY
```

可将输出与本文第 4 节 diff 对齐，或改为脚本直接生成 Markdown，避免清单与源码漂移。
