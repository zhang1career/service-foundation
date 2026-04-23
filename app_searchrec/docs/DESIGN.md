# SearchRec Design

## 1. 模块目标

`app_searchrec` 是一个搜索/推荐基础服务，面向业务系统提供稳定的通用能力：

- 文档索引写入（`POST /api/searchrec/index`）
- 搜索召回（`search`）
- 个性化推荐（`recommend`）
- 候选重排（`rank`）

业务系统只需要传业务数据和策略参数，不需要自己维护搜索/推荐底层技术细节。

## 2. 总体架构图

PlantUML 图：[`architecture_flow.puml`](./architecture_flow.puml)

## 3. 核心组件说明

- `views`：对外 API 层，负责参数接收和响应输出。
- `SearchRecService`：编排层，负责召回融合和最终打分。
- `adapters/index_store`：关键词检索适配器（memory/opensearch）。
- `adapters/vector_store`：向量召回适配器（memory/qdrant/milvus）。
- `adapters/feature_store`：在线特征适配器（memory/feast）。
- `adapters/embedding_provider`：文本向量生成能力（给向量检索适配器使用）。

## 4. 典型用例与活动图

下面用“业务动作 -> 基础服务动作”的方式，展示常见场景。

### 用例A：内容入库并可检索（运营发布内容）

**场景**：运营同学发布一批内容，业务系统调用 `POST /api/searchrec/index`，让内容进入搜索/推荐候选池。  
**价值**：保证后续搜索和推荐都能命中这批新内容。

PlantUML 图：[`usecase_a_upsert_flow.puml`](./usecase_a_upsert_flow.puml)

### 用例B：关键词搜索（用户主动查找）

**场景**：用户输入关键词，业务系统调用 `search`。  
**价值**：同时利用关键词和向量召回，再融合排序，提升结果相关性。

PlantUML 图：[`usecase_b_search_flow.puml`](./usecase_b_search_flow.puml)

### 用例C：个性化推荐（用户首页推荐流）

**场景**：用户打开首页，业务系统调用 `recommend`。  
**价值**：基于用户画像（偏好标签、最近查询）构造召回查询，并做个性化加权。

PlantUML 图：[`usecase_c_recommend_flow.puml`](./usecase_c_recommend_flow.puml)

### 用例D：候选重排（业务已有候选，交给基础服务排序）

**场景**：业务侧已经拿到候选（例如活动池），调用 `rank` 做统一打分。  
**价值**：统一排序策略，避免每个业务线重复实现打分逻辑。

PlantUML 图：[`usecase_d_rank_flow.puml`](./usecase_d_rank_flow.puml)

## 5. 给搜索新手的理解建议

- 搜索和推荐可以拆成三层：**召回 -> 特征 -> 排序**。
- 召回要“广”，排序要“准”，两者目标不同。
- 向量检索是“语义近似”，关键词检索是“字面匹配”，混合效果通常更好。
- Feature Store 负责统一管理在线特征，避免不同服务特征口径不一致。
- 业务系统只保留业务规则，本服务承接通用检索与排序能力。
