/**
 * 通用编辑弹窗，带回调钩子。
 * 使用：页面需包含 modal_edit.html 的 include，然后调用 ConsoleModal.open(options)。
 *
 * options: {
 *   id: string,           // 弹窗 DOM id（与 include 的 modal_id 一致）
 *   title: string,        // 标题
 *   bodyHtml?: string,   // 可选，打开时注入到弹窗 body 的 HTML
 *   initialValue?: any,  // 可选，打开时设置到 body 内 input/textarea 的值（若 body 中有 id 为 id+'-input' 的元素则自动设置）
 *   getValue: function(), // 保存时调用，返回当前表单值
 *   onSave: function(value), // 用户点击保存时调用，可 async
 *   onCancel: function(),   // 用户点击取消或遮罩时调用
 *   anchorEl?: Element,   // 可选，弹窗内容区将定位到该元素高度
 *   saveLabel?: string,  // 可选，保存按钮文字
 *   cancelLabel?: string // 可选，取消按钮文字
 * }
 */
var ConsoleModal = (function() {
    function open(options) {
        if (!options || !options.id) return;
        var id = options.id;
        var modal = document.getElementById(id);
        var backdrop = document.getElementById(id + '-backdrop');
        var content = document.getElementById(id + '-content');
        var titleEl = document.getElementById(id + '-title');
        var bodyEl = document.getElementById(id + '-body');
        var saveBtn = document.getElementById(id + '-save');
        var cancelBtn = document.getElementById(id + '-cancel');
        if (!modal || !content) return;

        if (options.title && titleEl) titleEl.textContent = options.title;
        if (options.bodyHtml && bodyEl) bodyEl.innerHTML = options.bodyHtml;
        if (options.initialValue !== undefined) {
            var input = bodyEl ? bodyEl.querySelector('#' + id + '-input') || bodyEl.querySelector('textarea') || bodyEl.querySelector('input') : null;
            if (input) input.value = options.initialValue;
        }
        if (options.saveLabel && saveBtn) saveBtn.textContent = options.saveLabel;
        if (options.cancelLabel && cancelBtn) cancelBtn.textContent = options.cancelLabel;

        if (options.anchorEl && content) {
            var rect = options.anchorEl.getBoundingClientRect();
            content.style.top = Math.max(16, rect.top) + 'px';
        }

        function close() {
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
        }

        function handleCancel() {
            close();
            if (typeof options.onCancel === 'function') options.onCancel();
        }

        function handleSave() {
            var value = typeof options.getValue === 'function' ? options.getValue() : undefined;
            var ret = typeof options.onSave === 'function' ? options.onSave(value) : undefined;
            if (ret && typeof ret.then === 'function') {
                if (saveBtn) saveBtn.disabled = true;
                ret.then(function() { close(); if (saveBtn) saveBtn.disabled = false; }).catch(function() { if (saveBtn) saveBtn.disabled = false; });
            } else {
                close();
            }
        }

        saveBtn.removeEventListener('click', saveBtn._consoleModalSave);
        cancelBtn.removeEventListener('click', cancelBtn._consoleModalCancel);
        backdrop.removeEventListener('click', backdrop._consoleModalCancel);
        saveBtn._consoleModalSave = handleSave;
        cancelBtn._consoleModalCancel = handleCancel;
        backdrop._consoleModalCancel = handleCancel;
        saveBtn.addEventListener('click', handleSave);
        cancelBtn.addEventListener('click', handleCancel);
        backdrop.addEventListener('click', handleCancel);

        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
    }

    function close(id) {
        var modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
        }
    }

    return { open: open, close: close };
})();
