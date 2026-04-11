# app_snowflake — Snowflake ID 设计说明

本文档从 `service-foundation-old` 的 Snowflake 设计说明提炼而来，并与**本仓库** `app_snowflake` 的实际实现一致；已省略旧文档中的示例代码、目录树与 FastAPI 专属细节。

---

## 1. 概述

### 1.1 服务定位

基于 Snowflake 思路的分布式唯一 ID 生成能力，作为 Django 应用挂载在统一网关路径下（根路径见项目 `service_foundation/urls.py` 中的 `api/snowflake/`）。

### 1.2 设计目标

- **唯一性**：在多实例、多机器部署下避免 ID 冲突（依赖数据中心/机器/重启计数等分段组合）。
- **高性能**：单机毫秒级可生成大量 ID（同毫秒内受序列位宽限制）。
- **有序性**：在时钟正常推进的前提下，ID 随时间大致递增。
- **可扩展**：通过环境变量区分实例的机房与机器号；水平扩展时需保证 **(datacenter_id, machine_id)** 组合唯一。
- **可用性**：生成逻辑集中在进程内；重启与时钟相关状态通过持久化与事件记录配合恢复（见下文）。

---

## 2. 算法与位布局

### 2.1 64 位整数结构（实现约定）

实现上将时间戳置于高位，低位依次为机房、机器、重启/回拨计数、业务段与毫秒内序列。具体位移与掩码见 `app_snowflake/consts/snowflake_const.py` 与 `SnowflakeGenerator` 中的组装公式。

各段含义（与实现一致）：

- **符号**：使用有符号 64 位整数的非负表示，高位为时间戳段，保证值为正。
- **时间戳（41 bit）**：相对配置的 **纪元起点**（毫秒）的偏移，纪元由 `SNOWFLAKE_START_TIMESTAMP` 指定。
- **数据中心 ID（2 bit）**：取值 0–3。
- **机器 ID（3 bit）**：取值 0–7。
- **重启/时钟回拨计数 recount（2 bit）**：取值 0–3，在重启或严重时钟回拨等路径上递增并持久化，用于降低冲突风险。
- **业务段（3 bit）**：取值 0–7；对调用方而言，由 **注册表主键 `rid` 经掩码** 参与编码（见「HTTP 接口」）。
- **序列（12 bit）**：同一毫秒内递增，单毫秒理论上限 4096；溢出时等待下一毫秒。

### 2.2 生成流程（逻辑要点）

1. 取得当前毫秒时间戳（相对 `start_timestamp`）。
2. 处理**首次生成/重启**与**时钟回拨**：小范围回拨可等待；超过阈值则更新 recount 并可能抛出时钟回拨异常（见 `ClockBackwardException` 与 `CLOCK_BACKWARD_THRESHOLD`）。
3. 同一毫秒内递增序列；跨毫秒则序列归零。
4. 序列绕回 0 时等待下一毫秒，并记录序列溢出类事件（若启用）。
5. 按位或组装 64 位 ID，并更新上次生成时间与序列状态（在锁内完成）。

### 2.3 关键问题处理

**时钟回拨**：每次生成比较当前时间与上次生成时间；小阈值内等待恢复；超出阈值则通过 recount 与事件处理，必要时对调用方返回业务错误码（见「错误码」）。

**序列**：同毫秒线性递增；与生成器锁配合保证线程安全。

**Recount（重启计数）**：目的为避免重启或异常时钟下的 ID 冲突；本实现通过 **`recounter` 数据表** 等与 `recounter_service` 协作持久化，**不使用**旧文档中的本地文件路径。

**并发**：`SnowflakeGenerator` 使用线程锁保护生成与状态更新。

---

## 3. HTTP 接口（本仓库）

- **生成单个 ID**：`POST /api/snowflake/id`  
  - 请求体 JSON 需提供 **`access_key`**。  
  - 服务在库 **`sf_snowflake`** 的 **`reg`** 表中按 `access_key` 与 **启用状态**（`status = 1`，与 `ServiceRegStatus.ENABLED` 一致）查询，得到主键 **`id` 作为 `rid`**。  
  - **`rid` 取代旧版 `bid`**，经掩码参与 Snowflake 业务段编码；响应 `data` 中含 **`rid`** 及解析得到的各段字段（含解码出的 3 位业务段 `business_id`）。  
  - 详细字段与包络格式见仓库根目录 `docs/api_snowflake.json`（OpenAPI）。

- **字典查询**：`GET /api/snowflake/dict?codes=...`  
  - 共用 `common` 的字典接口，枚举注册见 `dict_registration.py` 等。

统一响应包络为 **`errorCode` / `data` / `message`**（成功时 `errorCode = 0`），与项目其它微服务一致；**非**旧文档中的 `code` 字段名。

本应用**未**实现旧文档中的批量生成、独立 `info`、独立 `health` 等路由；若需健康检查，由上层网关或宿主项目统一提供。

---

## 4. 配置

通过 `app_snowflake/config.py` 读取环境变量（支持项目根 `.env` 分层加载）：

| 变量 | 含义 |
|------|------|
| `SNOWFLAKE_DATACENTER_ID` | 数据中心 ID，0–3 |
| `SNOWFLAKE_MACHINE_ID` | 机器 ID，0–7 |
| `SNOWFLAKE_START_TIMESTAMP` | 纪元起点（毫秒时间戳），默认与实现中常量一致 |

**时钟回拨容忍毫秒数**由代码常量 `CLOCK_BACKWARD_THRESHOLD` 定义（默认 5ms），**不是**环境变量。

数据库连接使用 Django 中 **`snowflake_rw`** 别名（见项目 `settings.py` 与 `db_routers.py`）。

---

## 5. 数据与持久化

- **`reg`**：调用方注册表；模型 `SnowflakeReg`（`managed = False`，表由运维/迁移维护），仅查询。  
- **`recounter`**：与数据中心、机器维度关联的计数状态，供 recount 逻辑使用。  
- **事件**：时钟回拨、序列溢出等通过 `event_service` / `event_repo` 写入事件表，便于运维追溯。

---

## 6. 错误码（与公共常量对齐）

- **成功**：`errorCode = 0`（`RET_OK`）。  
- **参数/注册**：如缺少 `access_key` 或无效/未启用的 access_key，使用 **`RET_INVALID_PARAM`（100）** 等（见 `common/consts/response_const.py`）。  
- **时钟回拨**：**`RET_SNOWFLAKE_CLOCK_BACKWARD`（1001）**。  

旧文档中列举的 1002–1004 等在本应用中**不一定**一一对应；以 `response_const` 与具体视图实现为准。

---

## 7. 模块结构（本应用内）

| 区域 | 职责 |
|------|------|
| `services/snowflake_generator.py` | 核心位运算与生成、解析 |
| `services/snowflake_service.py` | 对外的单 ID 组装结果（含 `rid` 等字段） |
| `services/recounter_service.py` / `repos/recounter_repo.py` | recount 持久化 |
| `services/event_service.py` / `repos/event_repo.py` | 事件记录 |
| `repos/reg_repo.py` | 按 access_key + status 查询注册 |
| `models/reg.py` / `models/recounter.py` / `models/event.py` | ORM 映射 |
| `views/snowflake_view.py` | HTTP 入口 |
| `exceptions/` | 时钟回拨、配置等异常 |
| `consts/snowflake_const.py` | 位宽、掩码、阈值 |

---

## 8. 性能、监控与测试（原则）

- **性能**：目标与优化手段（锁粒度、批量等）可参考旧文档思路；本实现以同步 Django/DRF 为主，实际指标需结合部署压测。  
- **监控**：可关注生成 QPS、延迟、时钟回拨与序列溢出事件、DB 可用性等。  
- **测试**：`app_snowflake/tests/` 下含生成器、recounter、视图等测试；集成测试依赖 `snowflake_rw` 等数据库配置。

---

## 9. 部署与扩展注意

- 多实例部署时，必须为每个实例配置 **互不冲突** 的 `SNOWFLAKE_DATACENTER_ID` / `SNOWFLAKE_MACHINE_ID`。  
- 调用方在 **`reg`** 中维护 **唯一 `access_key`** 与 **启用状态**；生成侧只认启用记录。  
- 业务段仅 3 位，**`rid` 实际参与编码的是与掩码按位与后的值**；大 `rid` 可能映射到同一业务段，需在业务上接受或另行设计。

---

## 10. 风险与缓解（摘要）

| 风险 | 缓解思路 |
|------|----------|
| 时钟大幅回拨 | 检测、recount、错误码返回，由调用方重试或告警 |
| 机器号配置冲突 | 部署规范与配置校验 |
| 同毫秒序列耗尽 | 等待下一毫秒（实现内处理） |
| 高并发锁竞争 | 压测评估；必要时再考虑无锁或分段等优化 |

---

## 11. 参考

- Twitter Snowflake 经典思路（本实现为项目定制位宽与持久化策略）。  
- 美团 Leaf 等分布式 ID 方案对比（概念参考）。  

---

*文档由旧版设计说明迁移并裁剪；实现以代码与 `docs/api_snowflake.json` 为准。*
