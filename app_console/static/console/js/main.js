// Console App JavaScript

// HTMX configuration
document.body.addEventListener('htmx:configRequest', function(evt) {
    // Add CSRF token to all HTMX requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        evt.detail.headers['X-CSRFToken'] = csrfToken;
    }
});

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', function(evt) {
    const status = evt.detail.xhr.status;
    let message = '操作失败';
    
    if (status === 404) {
        message = '资源不存在';
    } else if (status === 403) {
        message = '没有权限';
    } else if (status === 500) {
        message = '服务器错误';
    }
    
    showToast(message, 'error');
});

// Handle HTMX after swap for success messages
document.body.addEventListener('htmx:afterSwap', function(evt) {
    const trigger = evt.detail.requestConfig?.triggeringEvent?.target;
    if (trigger?.dataset?.successMessage) {
        showToast(trigger.dataset.successMessage, 'success');
    }
});

/**
 * 控制台唯一通知：顶部右侧 toast（移入/移出），success=绿 / info=蓝 / warning=黄，约 3 秒消失；error=弹窗确认。
 * Usage: showToast('message', 'success' | 'info' | 'warning' | 'error')
 */
function showToast(message, type = 'info') {
    if (type === 'error') {
        showErrorModal(message);
        return;
    }

    const container = document.getElementById('toast-container');
    if (!container) return;

    // 延后一帧再插入 DOM，避免在关弹窗/刷新列表后立刻调用时被遮挡或未绘制
    requestAnimationFrame(function() {
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(function() {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(function() {
                if (toast.parentNode) container.removeChild(toast);
            }, 300);
        }, 3000);
    });
}

/**
 * Show error modal: light red background, stays open until user clicks 确认.
 */
function showErrorModal(message) {
    const existing = document.getElementById('console-error-modal-backdrop');
    if (existing) existing.remove();

    const backdrop = document.createElement('div');
    backdrop.id = 'console-error-modal-backdrop';
    backdrop.className = 'console-modal-backdrop';

    const box = document.createElement('div');
    box.className = 'console-modal-error';
    box.innerHTML = `
        <div class="console-modal-message">${escapeHtml(String(message || ''))}</div>
        <button type="button" class="console-modal-confirm">确认</button>
    `;

    const btn = box.querySelector('.console-modal-confirm');
    function close() {
        backdrop.remove();
    }
    btn.addEventListener('click', close);
    attachModalBackdropClose(backdrop, close);

    backdrop.appendChild(box);
    document.body.appendChild(backdrop);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * 点击遮罩关闭弹窗。
 * 若仅用 click 且 e.target===backdrop，从弹窗内拖选文本到遮罩外松开时，click 可能落在遮罩上导致误关。
 * 改为：仅当 mousedown 与 mouseup 的 target 均为该 backdrop 时才关闭（主键左键）。
 */
function attachModalBackdropClose(backdropEl, closeFn) {
    if (!backdropEl || typeof closeFn !== 'function') return;
    let startOnBackdrop = false;
    backdropEl.addEventListener('mousedown', function (e) {
        if (e.button !== 0) return;
        startOnBackdrop = e.target === backdropEl;
    });
    backdropEl.addEventListener('mouseup', function (e) {
        if (e.button !== 0) return;
        if (startOnBackdrop && e.target === backdropEl) {
            closeFn();
        }
        startOnBackdrop = false;
    });
}

// Confirm dialog helper
function confirmAction(message) {
    return confirm(message);
}

// Format date helper
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Copy to clipboard helper
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败', 'error');
    });
}

/**
 * 与「仅列表→编辑」相关的固定文案（详情页勿引导去编辑；提示用户回列表时用）。
 * 新模块如需同类提示，在此追加键值，避免模板/脚本各处硬编码不一致。
 */
var ConsoleNavStrings = {
    hintBatchEditFromListFirst: '请先在「批次列表」中通过编辑入口填写内容后再分析'
};

/**
 * 返回列表：仅当 referrer 表明「从列表页点进当前页」时用 history.back（保留筛选/分页等）；
 * referrer 为空、与当前页相同（刷新后常见）或非列表时，用 location.replace，避免误 back 或 href 叠栈。
 */
function returnToList(fallbackUrl) {
    var fallback = String(fallbackUrl || '').trim() || '/console/';
    var here;
    try {
        here = new URL(window.location.href);
    } catch (e) {
        window.location.replace(fallback);
        return false;
    }
    var fall;
    try {
        fall = new URL(fallback, window.location.origin);
    } catch (e) {
        window.location.replace(fallback);
        return false;
    }
    function normPath(p) {
        var s = p && p !== '/' ? String(p) : '/';
        if (s.length > 1) s = s.replace(/\/+$/, '');
        return s || '/';
    }
    if (!document.referrer) {
        window.location.replace(fallback);
        return false;
    }
    var ref;
    try {
        ref = new URL(document.referrer);
    } catch (e) {
        window.location.replace(fallback);
        return false;
    }
    if (ref.origin !== window.location.origin) {
        window.location.replace(fallback);
        return false;
    }
    if (normPath(ref.pathname) === normPath(here.pathname) && ref.search === here.search) {
        window.location.replace(fallback);
        return false;
    }
    if (normPath(ref.pathname) === normPath(fall.pathname) && window.history.length > 1) {
        window.history.back();
        return false;
    }
    window.location.replace(fallback);
    return false;
}

/**
 * 刷新当前控制台页面（完整重载）。与「表单 POST 后服务端 302 回到本页」效果相同；fetch 场景可在成功后调用。
 */
function reloadConsolePage() {
    window.location.reload();
}

// API helper for fetch requests
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        options.headers['X-CSRFToken'] = csrfToken;
    }
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '请求失败');
        }
        
        return result;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// Global ESC key: close any visible modal (use capture so we run before focused input/textarea)
document.addEventListener('keydown', function(e) {
    if (e.key !== 'Escape') return;
    // Error modal: click confirm button to close
    var errModal = document.getElementById('console-error-modal-backdrop');
    if (errModal) {
        var btn = errModal.querySelector('.console-modal-confirm');
        if (btn) btn.click();
        return;
    }
    // .modal-backdrop：仅用 .hidden（style.css 中已有 display:none !important），勿写行内 display，否则再次打开弹层无法显示
    document.querySelectorAll('.modal-backdrop:not(.hidden)').forEach(function (m) {
        m.classList.add('hidden');
    });
}, true);  // capture phase: run before event reaches focused input/textarea

/**
 * 主题切换：light=护眼绿 / dark=深灰，状态持久化到 localStorage
 * 可在非 base 页面单独调用 ConsoleApp.initTheme() 复用
 */
function initTheme() {
    var KEY = 'console-theme';
    var DARK = 'dark', LIGHT = 'light';

    function getStored() {
        try {
            return localStorage.getItem(KEY) || LIGHT;
        } catch (e) {
            return LIGHT;
        }
    }
    function setStored(v) {
        try { localStorage.setItem(KEY, v); } catch (e) {}
    }
    function apply(theme) {
        var isDark = theme === DARK;
        document.documentElement.classList.toggle('theme-dark', isDark);
        var cb = document.getElementById('theme-toggle');
        if (cb) cb.checked = !isDark;
    }

    var initial = getStored();
    apply(initial);

    var cb = document.getElementById('theme-toggle');
    if (cb) {
        cb.addEventListener('change', function() {
            var theme = this.checked ? LIGHT : DARK;
            setStored(theme);
            apply(theme);
        });
    }
}

/**
 * 侧边栏折叠/拖拽：状态持久化到 localStorage
 * 可在非 base 页面单独调用 ConsoleApp.initSidebar() 复用
 */
function initSidebar() {
    var SIDEBAR_KEY = 'console_sidebar_collapsed';
    var SIDEBAR_EXPANDED = 256;
    var SIDEBAR_COLLAPSED = 64;
    var sidebar = document.getElementById('console-sidebar');
    var handle = document.getElementById('sidebar-handle');
    var toggleBtn = document.getElementById('sidebar-toggle');
    var iconExpand = document.getElementById('sidebar-toggle-icon-expand');
    var iconCollapse = document.getElementById('sidebar-toggle-icon-collapse');

    if (!sidebar) return;

    function isCollapsed() {
        return localStorage.getItem(SIDEBAR_KEY) === '1';
    }
    function setCollapsed(collapsed) {
        localStorage.setItem(SIDEBAR_KEY, collapsed ? '1' : '0');
    }
    function applyState() {
        var collapsed = isCollapsed();
        var footerShort = document.getElementById('sidebar-footer-short');
        if (collapsed) {
            sidebar.classList.add('sidebar-collapsed');
            sidebar.style.setProperty('--sidebar-width', SIDEBAR_COLLAPSED + 'px');
            document.querySelectorAll('.sidebar-text').forEach(function(el) { el.classList.add('hidden'); });
            var logoText = document.getElementById('sidebar-logo-text');
            var logoIcon = document.getElementById('sidebar-logo-icon');
            if (logoText) logoText.classList.add('hidden');
            if (logoIcon) logoIcon.classList.remove('hidden');
            if (footerShort) footerShort.classList.remove('hidden');
            if (iconExpand) iconExpand.classList.remove('hidden');
            if (iconCollapse) iconCollapse.classList.add('hidden');
            if (toggleBtn) toggleBtn.title = '展开';
        } else {
            sidebar.classList.remove('sidebar-collapsed');
            sidebar.style.setProperty('--sidebar-width', SIDEBAR_EXPANDED + 'px');
            document.querySelectorAll('.sidebar-text').forEach(function(el) { el.classList.remove('hidden'); });
            var logoText = document.getElementById('sidebar-logo-text');
            var logoIcon = document.getElementById('sidebar-logo-icon');
            if (logoText) logoText.classList.remove('hidden');
            if (logoIcon) logoIcon.classList.add('hidden');
            if (footerShort) footerShort.classList.add('hidden');
            if (iconExpand) iconExpand.classList.add('hidden');
            if (iconCollapse) iconCollapse.classList.remove('hidden');
            if (toggleBtn) toggleBtn.title = '折叠';
        }
    }
    function toggle() {
        setCollapsed(!isCollapsed());
        applyState();
    }

    if (toggleBtn) toggleBtn.addEventListener('click', toggle);

    var dragStartX = 0, dragStartW = 0;
    if (handle) {
        handle.addEventListener('mousedown', function(e) {
            e.preventDefault();
            dragStartX = e.clientX;
            dragStartW = isCollapsed() ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED;
            document.addEventListener('mousemove', onDrag);
            document.addEventListener('mouseup', onDragEnd);
        });
    }
    function onDrag(e) {
        var delta = e.clientX - dragStartX;
        var newW = Math.max(SIDEBAR_COLLAPSED, Math.min(SIDEBAR_EXPANDED, dragStartW + delta));
        if (newW <= SIDEBAR_COLLAPSED + 20) {
            setCollapsed(true);
            applyState();
        } else if (newW >= SIDEBAR_EXPANDED - 20) {
            setCollapsed(false);
            applyState();
        }
    }
    function onDragEnd() {
        document.removeEventListener('mousemove', onDrag);
        document.removeEventListener('mouseup', onDragEnd);
    }

    applyState();
}

// 命名空间，便于其他页面按需调用
var ConsoleApp = { initTheme: initTheme, initSidebar: initSidebar, returnToList: returnToList, strings: ConsoleNavStrings };

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSidebar();
    console.log('Console app initialized');
});
