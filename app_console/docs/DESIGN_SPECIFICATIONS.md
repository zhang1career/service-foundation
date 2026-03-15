# 控制台设计约定

## 编辑页与保存行为

1. **从列表点击编辑进入编辑页**：
   - **保存**：提交表单后，成功则跳转到**详情页**；失败则**停留在编辑页**，不跳转。
   - **取消**：返回**列表页**（不进入详情页）。

2. **保存操作（表单提交）的通知**：
   - 所有保存操作（提交表单）在**成功**或**失败**时都应在屏幕顶部展示通知。
   - 使用顶部通知条：`showTopNotice(message, 'success' | 'warning' | 'error')`（见下）。

## 顶部通知条（全页面复用）

- **组件**：base 中提供 `#console-top-notice`，默认不显示。由 `main.js` 的 `showTopNotice(message, type)` 控制。
- **类型与颜色**：`success` 绿、`warning` 黄、`error` 红；约 3 秒后自动隐藏。
- **用法**：任意页面直接调用 `showTopNotice('提示文案', 'success' | 'warning' | 'error')`，无需再写 DOM 或样式。
- **不阻塞**：仅展示提示，不阻塞跳转或操作。

---

## 列表页 UI 约定

- **查看**：不提供「查看」按钮。点击列表项的主列（标题/名称/内容）链接进入详情页。
- **删除**：仅使用图标（垃圾桶），`title="删除"`，样式 `btn-danger btn-sm p-1.5`。
- **编辑**：仅使用图标（铅笔），`title="编辑"`，样式 `btn-outline btn-sm p-1.5`。

## 公用逻辑

- 主列可点击：使用 `listTitleCell(text, detailUrl)` 渲染，点击进入详情。
- 操作列：使用 `listActions({ id, onEdit?, onDelete?, extra? })` 渲染编辑/删除图标及可选额外按钮。
- 脚本：`console/js/list-actions.js` 在 base 中已引入，各列表页可直接使用上述函数。

## 使用示例

```javascript
// 主列：点击进入详情
${listTitleCell(item.title, '/console/xxx/' + item.id + '/')}

// 操作列：仅删除
${listActions({ id: item.id, onDelete: 'deleteXxx' })}

// 操作列：编辑 + 删除
${listActions({ id: item.id, onEdit: 'editXxx', onDelete: 'deleteXxx' })}

```
