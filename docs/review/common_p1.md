# `common` P1 架构评审

对照 `docs/plan/REVIEW_common.md` **第 7 节「建议执行顺序」**中 **P1 架构** 的三项：`AigcAPI` 归属、`DictCodesView` 假设、`django_util.post_to_dict` 契约。评价维度与 `REVIEW_common.md` **§1～3** 一致（完善度、独立性、边界、性能、安全、在分层中的角色），结论采用「通过 / 待改进 / 阻塞」。

---

## 1. `AigcAPI`（`common/apis/aigc_api.py`）

### 在架构中的角色

- 对 **OpenAI 兼容上游** 做 JSON POST，解析 chat / image / video / embedding 响应；依赖 `AIGC_API_URL` / `AIGC_API_KEY`（或构造参数）与 `common.services.http.request_sync`、`HttpClientPool.THIRD_PARTY`。
- 与 `common/docs/TODO.md` P1-6 及仓库规则一致：**绑定具体上游形态与 `AIGC_*` 配置**，属于「领域出站 HTTP」，更自然的归属是**拥有调用链的应用**（当前实际调用集中在 `app_aibroker.services.llm_client_service`）。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | `invoke` 对各 op 分支清晰；HTTP 非 2xx 时从 body 取 `error` 信息；JSON 非法时降级为空 dict 再判错，可能掩盖上游返回非 JSON 的根因。超时固定 `_AIGC_TIMEOUT_SEC = 120`，未与 settings 对齐。 |
| **独立性** | 依赖 Django `settings`（经 `effective_setting_str`）、进程内 HTTP 池；单测需 patch settings/传输层，与 `REVIEW_common.md` §5.10 预期一致。`Singleton` 元类按 `args/kwargs` 哈希分实例，**不同 provider 参数会得到不同实例**，与「全局单例误绑多租户」类问题不冲突。 |
| **边界清晰度** | **待改进**：放在 `common.apis` 使「通用原语」与「AIGC 上游契约」混在同一包路径下；迁出后 `common` 仅保留 `request_sync` 等传输原语更清晰。未反向依赖 `app_*`。 |
| **性能** | 热路径为单次请求；无额外循环内 I/O。 |
| **安全** | URL 来自配置的 `base_url` + 调用方 `path`；SSRF 防护落在通用 HTTP 层策略（见 P0），此处不重复展开。`Authorization` 经 `request_sync` 传出，需与全局敏感日志策略一致。 |

### 结论

**待改进**（架构归属，非功能阻塞）。与 `REVIEW_common.md` §5.10、`common/docs/TODO.md` P1-6 一致：若团队采纳「领域出站 HTTP 在拥有应用」，宜将 `AigcAPI` 迁至 **`app_aibroker`（或统一 AIGC 网关的单一应用包）**，`common` 保留与上游无关的 HTTP 工具；`AigcInvokeOp` 等枚举可随迁移或留在 common 视团队对「共享枚举」的约定而定。

---

## 2. `DictCodesView`（`common/views/dict_codes_view.py`）

### 在架构中的角色

- DRF `APIView`：GET `?codes=`，调用 `get_dict_by_codes` 返回字典元数据；被多个应用挂载为 `.../dict`（如 `app_user`、`app_aibroker`、`service_foundation.urls` 的 `api/cdn/dict` 等），属于 **跨应用复用的只读字典查询端点**。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 缺少 `codes` 时返回 `RET_MISSING_PARAM`；成功路径明确。 |
| **独立性** | 依赖 `dict_catalog` 与统一响应封装，可测性取决于 `get_dict_by_codes` 是否易 mock。 |
| **边界清晰度** | 视图放在 `common.views` 与「共享 HTTP 边界」一致；**产品安全假设需由部署侧保证**（见下）。 |
| **性能** | 典型为小查询；若 `codes` 极大或目录很重，宜在目录层设上限（属增强项，非本节必评）。 |
| **安全** | `authentication_classes = []`、`permission_classes = []`：**公开只读接口**，与 `REVIEW_common.md` §5.6、`common/docs/TODO.md` P1-9 所列一致——需产品确认（仅内网、网关鉴权、或 CDN 可接受匿名）。异常分支 `resp_err(..., message=str(e))` **始终**把 `Exception` 文本返回客户端；`resp_err` 本身不像 `resp_exception` 那样用 `DEBUG` 区分，存在 **信息泄露** 风险（内部异常细节暴露给任意调用方）。 |

### 结论

**待改进**。架构上「共享字典视图」合理，但 **匿名 + 多应用挂载** 的假设必须在 **部署/网关/网络** 层可验证；代码侧建议将异常响应改为通用文案或受 `DEBUG` 控制的细节（与 P1-9 对齐），避免 `str(e)` 直出。

---

## 3. `post_to_dict`（`common/utils/django_util.py`）

### 在架构中的角色

- 命名与模块（`django_util`）暗示 **Django 通用**，实现却使用 **`request.data`**（DRF Request），对纯 Django `HttpRequest` **不适用**。

### 各维度摘要

| 维度 | 说明 |
|------|------|
| **完善度** | 仅遍历 `request.data` 取单值；未处理多值键、与 `post_like_mapping_to_dict` 的 QueryDict 语义未统一。 |
| **独立性** | 强依赖 DRF 请求对象。 |
| **边界清晰度** | **待改进**：契约与命名不符；`common/docs/TODO.md` P1-7 要求 **改名或拆分为 DRF 专用并文档化前置条件**。 |
| **性能 / 安全** | 无显著热点；无额外安全风险。 |

### 代码引用

```39:49:common/utils/django_util.py
def post_to_dict(request):
    """
    Convert post data to dict
    """
    data = {}

    # get param
    for key in request.data.keys():
        data[key] = request.data.get(key)

    return data
```

### 结论

**待改进**。当前仓库内 **未发现其它模块引用 `post_to_dict`**（仅定义处），要么是遗留未用 API，要么是计划给业务用但未落地。无论哪种，均建议按 P1-7 **重命名**（例如 `drf_request_data_to_dict`）或迁入 DRF 相关工具模块，并在 docstring 写明 **参数须为 DRF Request**；若确认无调用方可评估删除或保留为兼容别名（需团队策略）。

---

## 4. 小结（P1 架构项）

| 项 | 结论 | 与计划文档对应 |
|----|------|----------------|
| `AigcAPI` 归属 | **待改进**：宜迁到以 `app_aibroker` 为代表的拥有应用，`common` 保留通用传输。 | `REVIEW_common.md` §7 项 2；§5.10；`TODO.md` P1-6 |
| `DictCodesView` 假设 | **待改进**：公开端点的产品/网络安全假设需落地；异常信息不宜直出 `str(e)`。 | §7 项 2；§5.6；`TODO.md` P1-9 |
| `post_to_dict` 契约 | **待改进**：DRF 专用与命名/文档不一致；当前无引用，宜改名或移除并文档化。 | §7 项 2；§5.6；`TODO.md` P1-7 |

三项均无「阻塞级」架构断裂（例如 `common` 导入 `app_*`），但 **边界清晰度与安全细节** 与计划中的 P1 条目一致，建议在触及相关模块时按 `common/docs/TODO.md` 渐进收敛。
