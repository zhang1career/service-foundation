# 控制台设计约定

## 编辑页与保存行为

1. **编辑页仅允许从列表页进入**：
   - 详情页不允许提供任何编辑入口（按钮、链接、跳转逻辑均不允许）。
   - 编辑页的顶部“返回”与“取消”都只能回到列表页。
   - 编辑保存成功后返回列表页；失败停留编辑页并提示。

2. **详情页只作为列表页的子页**：
   - 详情页顶部“返回”只能回列表页，不跳转到其他页面。

3. **新建页行为**：
   - 新建页/新建弹层点击“取消”或“确认”后都应回到列表页。

4. **保存操作（表单提交）的通知**：
   - 所有保存操作在**成功**或**失败**时都应用**同一套通知**展示（见下）。

5. **导航记忆（保留）**：
   - `main.js` 的 `returnToList(fallbackUrl)`：仅当 `document.referrer` 与当前页不同、且其 path 与列表 `fallbackUrl` 的 path 一致（search 可不同，以保留 `?page=` 等）时，才 `history.back()`。
   - `referrer` 为空、与当前 URL 相同（常见于刷新后）、或来源非该列表时，使用 `location.replace(fallbackUrl)`，避免历史栈被「假返回」叠高。

## 通知（全控制台唯一）

- **唯一方式**：`main.js` 的 `showToast(message, type)`，顶部右侧移入/移出的 toast；`error` 为弹窗确认。
- **类型**：`success` 绿、`info` 蓝、`warning` 黄（约 3 秒消失）；`error` 红色弹窗（需点确认）。
- **用法**：任意页面统一调用 `showToast('提示文案', 'success' | 'info' | 'warning' | 'error')`。若需在跳转后的目标页展示一次性提示，可在目标页 load 后检测 URL 参数并 `showToast`，再 `history.replaceState` 清理参数。

---

## 列表页 UI 约定

- **查看**：不提供「查看」按钮。点击列表项的主列（标题/名称/内容）链接进入详情页。
- **删除**：仅使用图标（垃圾桶），`title="删除"`，样式 `btn-danger btn-sm p-1.5`。
- **编辑**：仅使用图标（铅笔），`title="编辑"`，样式 `btn-outline btn-sm p-1.5`。

## 公用逻辑

- 主列可点击：使用 `listTitleCell(text, detailUrl)` 渲染，点击进入详情。
- 操作列：使用 `listActions({ id, onEdit?, onDelete?, extra? })` 渲染编辑/删除图标及可选额外按钮。
- 脚本：`console/js/list-actions.js` 在 base 中已引入，各列表页可直接使用上述函数。

### 可复用模板片段（导航约定）

- **详情页顶部返回**：`console/includes/detail_back_link.html`（`back_url` = 列表页；已接 `returnToList`）。
- **列表页操作列铅笔**：`console/includes/list_edit_icon.html`（`edit_url` = 编辑页；**仅**列表使用，禁止在详情 include）。
- **新建模块自检注释**：`console/includes/console_nav_rules_comment.html`（整段为 `{% comment %}`，可复制到新建模板顶部作团队约定提醒，不参与渲染）。
- **脚本侧统一文案**：`console/js/main.js` 中的 `ConsoleNavStrings`（如「批次需先在列表编辑」等），避免在页面里重复写易分歧的句子。

## 使用示例

```javascript
// 主列：点击进入详情
${listTitleCell(item.title, '/console/xxx/' + item.id + '/')}

// 操作列：仅删除
${listActions({ id: item.id, onDelete: 'deleteXxx' })}

// 操作列：编辑 + 删除
${listActions({ id: item.id, onEdit: 'editXxx', onDelete: 'deleteXxx' })}

```
