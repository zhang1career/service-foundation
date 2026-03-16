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
