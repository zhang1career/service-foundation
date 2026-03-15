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
 * 屏幕顶部通知条（全页面复用）：默认不显示，调用时展示 success=绿 / warning=黄 / error=红，约 3 秒后自动隐藏。
 * 优先使用 base 中的 #console-top-notice，不存在时再动态创建一条。
 * Usage: showTopNotice('message', 'success' | 'warning' | 'error')
 */
function showTopNotice(message, type) {
    var colors = {
        success: { bg: '#059669', text: '#fff' },
        warning: { bg: '#d97706', text: '#fff' },
        error: { bg: '#dc2626', text: '#fff' }
    };
    var style = colors[type] || colors.success;
    var bar = document.getElementById('console-top-notice');
    if (bar) {
        bar.textContent = message;
        bar.style.background = style.bg;
        bar.style.color = style.text;
        bar.style.display = 'block';
        setTimeout(function() {
            bar.style.display = 'none';
        }, 3000);
        return;
    }
    bar = document.createElement('div');
    bar.setAttribute('role', 'alert');
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;padding:12px 16px;background:' + style.bg + ';color:' + style.text + ';font-size:14px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.15);';
    bar.textContent = message;
    document.body.insertBefore(bar, document.body.firstChild);
    setTimeout(function() {
        if (bar.parentNode) bar.remove();
    }, 3000);
}

/**
 * Show toast or modal notification (app_console shared component).
 *
 * - success: Light green toast, auto-dismiss 3s
 * - info: Blue toast, auto-dismiss 3s
 * - warning: Amber toast, auto-dismiss 3s
 * - error: Light red modal with confirm button, stays open until user clicks 确认
 *
 * Usage: showToast('message', 'success' | 'info' | 'warning' | 'error')
 */
function showToast(message, type = 'info') {
    if (type === 'error') {
        showErrorModal(message);
        return;
    }

    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            if (toast.parentNode) container.removeChild(toast);
        }, 300);
    }, 3000);
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
    backdrop.addEventListener('click', function (e) {
        if (e.target === backdrop) close();
    });

    backdrop.appendChild(box);
    document.body.appendChild(backdrop);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
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
    // .modal-backdrop (form modals): close by adding hidden + display:none
    var modals = document.querySelectorAll('.modal-backdrop:not(.hidden)');
    modals.forEach(function (m) {
        m.classList.add('hidden');
        m.style.display = 'none';
    });
}, true);  // capture phase: run before event reaches focused input/textarea

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here
    console.log('Console app initialized');
});
