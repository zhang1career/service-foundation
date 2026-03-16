# 控制台设计约定

## 编辑页与保存行为

1. **从列表点击编辑进入编辑页**：
   - **保存**：提交表单后，成功则跳转到**详情页**；失败则**停留在编辑页**，不跳转。
   - **取消**：返回**列表页**（不进入详情页）。

2. **保存操作（表单提交）的通知**：
   - 所有保存操作在**成功**或**失败**时都应用**同一套通知**展示（见下）。

## 通知（全控制台唯一）

- **唯一方式**：`main.js` 的 `showToast(message, type)`，顶部右侧移入/移出的 toast；`error` 为弹窗确认。
- **类型**：`success` 绿、`info` 蓝、`warning` 黄（约 3 秒消失）；`error` 红色弹窗（需点确认）。
- **用法**：任意页面统一调用 `showToast('提示文案', 'success' | 'info' | 'warning' | 'error')`。从它页跳转后提示（如编辑保存后带 `?saved=1` 进详情页）：目标页 load 后检测参数并调用 `showToast('已保存', 'success')`，再清理 URL。

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
