/**
 * app_console 列表操作风格：统一复用组件
 *
 * 规范：
 * - 标题/主标识列：可点击链接进入详情或子页面（无单独「查看」按钮）
 * - 操作列：编辑、删除
 */

/**
 * 相似度进度条：将 0～1 转为 0～100 的百分比字符串
 * @param {number} score - 相似度 0～1
 * @returns {string} 如 "85"
 */
function similarityProgressPct(score) {
    return Math.min(100, Math.max(0, (parseFloat(score) || 0) * 100)).toFixed(0);
}

/**
 * 渲染相似度进度条背景（公共逻辑，供 listTitleCellWithSimilarity、知识详情关系栏等复用）
 * @param {number} score - 相似度 0～1
 * @returns {string} HTML 字符串，需放在 position:relative; overflow:hidden 的容器内
 */
function renderSimilarityProgressBar(score) {
    const pct = similarityProgressPct(score);
    return `<div class="absolute inset-0 bg-blue-100 transition-all" style="width:${pct}%;" title="相似度 ${pct}%"></div>`;
}

/**
 * 渲染可点击的标题单元格（用于进入详情/子页面）
 * @param {string} text - 显示文本
 * @param {string} url - 目标链接
 * @param {string} [cssClass='font-medium'] - 额外 CSS 类
 * @returns {string} HTML 字符串
 */
function listTitleCell(text, url, cssClass = 'font-medium') {
    const display = text || '-';
    const escaped = String(display).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const escapedUrl = String(url || '').replace(/"/g, '&quot;');
    return `<td class="${cssClass}"><a href="${escapedUrl}" class="text-blue-600 hover:underline cursor-pointer">${escaped}</a></td>`;
}

/**
 * 渲染可点击的标题单元格，当有 similarity 时显示相似度进度条背景
 * @param {string} text - 显示文本
 * @param {string} url - 目标链接
 * @param {number|undefined|null} similarity - 相似度 0～1，仅在有值且为摘要筛选结果时显示进度条
 * @param {string} [cssClass='font-medium'] - 额外 CSS 类
 * @returns {string} HTML 字符串
 */
function listTitleCellWithSimilarity(text, url, similarity, cssClass = 'font-medium') {
    if (similarity == null || similarity === undefined) {
        return listTitleCell(text, url, cssClass);
    }
    const display = text || '-';
    const escaped = String(display).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    const escapedUrl = String(url || '').replace(/"/g, '&quot;');
    const bar = renderSimilarityProgressBar(similarity);
    return `<td class="${cssClass}"><a href="${escapedUrl}" class="text-blue-600 hover:underline cursor-pointer block relative overflow-hidden">
        ${bar}
        <span class="relative z-10">${escaped}</span>
    </a></td>`;
}

/**
 * 渲染普通标题单元格（不可点击）
 * @param {string} text - 显示文本
 * @param {string} [cssClass='font-medium'] - 额外 CSS 类
 * @returns {string} HTML 字符串
 */
function listPlainCell(text, cssClass = 'font-medium') {
    const display = text || '-';
    const escaped = String(display).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    return `<td class="${cssClass}">${escaped}</td>`;
}

/**
 * 渲染操作列：编辑 + 删除（无「查看」按钮）
 * @param {Object} opts
 * @param {number|string} opts.id - 记录 ID
 * @param {string} opts.onEdit - 编辑函数名（全局调用，如 'editKnowledge'）
 * @param {string} opts.onDelete - 删除函数名（全局调用，如 'deleteKnowledge'）
 * @param {Array<{label: string, onclick: string}|{label: string, href: string}>} [opts.extra] - 额外按钮
 * @returns {string} HTML 字符串
 */
function listActions(opts) {
    const { id, onEdit, onDelete, extra = [] } = opts;
    const idStr = String(id);
    let html = '<td><div class="flex space-x-2">';

    (extra || []).forEach((btn) => {
        if (btn.href) {
            html += `<a href="${String(btn.href).replace(/"/g, '&quot;')}" class="btn btn-outline btn-sm">${escapeHtml(btn.label)}</a>`;
        } else {
            html += `<button onclick="${escapeHtml(btn.onclick || '')}" class="btn btn-outline btn-sm">${escapeHtml(btn.label)}</button>`;
        }
    });

    if (onEdit) {
        html += `<button type="button" onclick="${String(onEdit)}(${idStr})" class="btn btn-outline btn-sm p-1.5" title="编辑"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg></button>`;
    }
    if (onDelete) {
        html += `<button type="button" onclick="${String(onDelete)}(${idStr})" class="btn btn-danger btn-sm p-1.5" title="删除"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button>`;
    }

    html += '</div></td>';
    return html;
}

/**
 * 渲染分页控件
 * @param {Object} opts
 * @param {number} opts.current_page
 * @param {number} opts.total_pages
 * @param {string} opts.loadFn - 翻页时调用的函数名，接收 page 参数
 * @returns {string} HTML 字符串
 */
function renderPagination(opts) {
    const { current_page, total_pages, loadFn } = opts;
    if (!total_pages || total_pages <= 1) return '';

    let html = '<div class="pagination">';
    html += `<button class="pagination-btn" ${current_page <= 1 ? 'disabled' : ''} onclick="${loadFn}(${current_page - 1})">上一页</button>`;
    for (let i = 1; i <= Math.min(total_pages, 5); i++) {
        html += `<button class="pagination-btn ${i === current_page ? 'active' : ''}" onclick="${loadFn}(${i})">${i}</button>`;
    }
    html += `<button class="pagination-btn" ${current_page >= total_pages ? 'disabled' : ''} onclick="${loadFn}(${current_page + 1})">下一页</button>`;
    html += '</div>';
    return html;
}
