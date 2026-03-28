# app_aibroker — TODO（提示词工程 / Prompt 能力）

与成熟提示词工程实践相比，当前实现的已知缺口。按需排期，非全部必须实现。

## 变量与 schema

- [ ] **`input_variables` 未参与运行时**：字段已存库，生成路径未按 schema 校验 `variables`（类型、必填、枚举等）。建议在保存与调用前校验，避免线上才因 `format` 或语义错误失败。

## 输出约束

- [ ] **`output_variables` 校验过弱**：仅检查 `[{"name":...}]` 所列键在模型 JSON 对象上存在，无完整 JSON Schema（类型、嵌套、格式）。
- [ ] **校验失败无恢复路径**：无自动重试或带 schema 违例信息的纠错再生成；可与模型原生 structured output / JSON mode 对齐。

## 对话与 API 形态

- [ ] **单条 user 消息**：整段 prompt 塞进一个 `user` content，无显式 system/developer、多轮 `messages`、assistant 前缀续写等拆分。
- [ ] **生成参数暴露少**：除 `temperature` 外，常见缺口包括 `max_tokens`、`top_p`、`stop`、`response_format`（如 JSON mode）、tools/function calling、部分模型的 reasoning 类开关等。

## 评测与发布

- [ ] **无模板版本级评测闭环**：缺回归用例集、离线/在线指标、A/B 或 shadow 等一等公民支持（可依赖外部产品或自建管线）。

## 可观测性

- [ ] **偏调用日志，非提示词工程视图**：可补充完整 prompt 快照、token 用量、分阶段耗时、模板版本标签等，便于非开发角色分析与排障。

## 组合与安全

- [ ] **无结构化拼装抽象**：few-shot 块、工具结果、RAG 片段等仅靠模板正文手写字符串，无组合块或链式编排（编排若属其他服务可注明边界）。
- [ ] **变量注入与安全**：`str.format(**variables)` 将调用方变量拼入模板；若存在不可信输入，需评估 instruction 隔离、越狱/注入策略与可选清洗层。

---

*来源：对当前 `template_render_service`、`text_generation_service`、`llm_client_service`、`PromptTemplate` 模型与 `AigcBestAPI.chat` 行为的代码审阅归纳。*
