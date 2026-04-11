/**
 * 运行监控页：异步拉取 /console/api/monitoring/snapshot/ 并渲染；可选定时刷新。
 */
(function () {
  "use strict";

  function escapeHtml(s) {
    if (s == null || s === "") return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function iconSvg(icon) {
    var common = ' class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"';
    var paths = {
      book:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>',
      mail:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>',
      folder:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>',
      hash:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"></path>',
      globe:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0h.5a2.5 2.5 0 002.5-2.5V8m-6.5 12.06V16.5a2.5 2.5 0 002.5-2.5V12M20.945 13H19a2 2 0 00-2 2v1a2 2 0 01-2 2 2 2 0 01-2-2v-2.945M16 20.065V19a2 2 0 012-2h2a2 2 0 012 2v1.065"></path>',
      user:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A9.953 9.953 0 0112 15c2.154 0 4.149.68 5.879 1.835M15 8a3 3 0 11-6 0 3 3 0 016 0z"></path>',
      bell:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>',
      shield:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3l7 4v5c0 5-3.5 8.5-7 9-3.5-.5-7-4-7-9V7l7-4z"></path>',
      sparkles:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>',
      search:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 100-15 7.5 7.5 0 000 15z"></path>',
      collection:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>',
      connect:
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>',
    };
    var p = paths[icon] || paths.globe;
    return "<svg" + common + ">" + p + "</svg>";
  }

  function httpProbeRow(hp) {
    if (!hp) {
      return '<span class="text-gray-500">—</span>';
    }
    if (hp.ok) {
      return (
        '<span class="badge badge-success">HTTP ' +
        escapeHtml(String(hp.status_code || "")) +
        '</span> <span class="monitoring-mono text-xs">' +
        escapeHtml(String(hp.ms)) +
        " ms</span>"
      );
    }
    return (
      '<span class="badge badge-error">失败</span> <span class="monitoring-mono text-xs text-red-600">' +
      escapeHtml(hp.error || hp.ms + " ms") +
      "</span>"
    );
  }

  function renderInfra(m, mount) {
    var rows = [];
    var rc = m.redis_cache || {};
    rows.push(
      "<tr><td class=\"font-medium\">Redis（Django cache）</td><td>" +
        (rc.ok
          ? '<span class="badge badge-success">正常</span>'
          : '<span class="badge badge-error">异常</span>') +
        '</td><td class="monitoring-mono monitoring-cell-detail">' +
        escapeHtml(String(rc.ms)) +
        " ms" +
        (rc.error ? " — " + escapeHtml(rc.error) : "") +
        "</td></tr>"
    );

    var mysql = m.mysql || {};
    Object.keys(mysql).forEach(function (alias) {
      var row = mysql[alias];
      rows.push(
        "<tr><td class=\"font-medium\">MySQL <code class=\"monitoring-inline-code\">" +
          escapeHtml(alias) +
          "</code></td><td>" +
          (row.ok
            ? '<span class="badge badge-success">正常</span>'
            : '<span class="badge badge-error">异常</span>') +
          '</td><td class="monitoring-mono monitoring-cell-detail">' +
          escapeHtml(String(row.ms)) +
          " ms" +
          (row.error ? " — " + escapeHtml(row.error) : "") +
          "</td></tr>"
      );
    });

    var neo = m.neo4j || {};
    var neoCell;
    if (neo.skipped) {
      neoCell = '<span class="badge badge-warning">跳过</span>';
    } else if (neo.ok) {
      neoCell = '<span class="badge badge-success">正常</span>';
    } else {
      neoCell = '<span class="badge badge-error">异常</span>';
    }
    var neoDetail = neo.skipped
      ? escapeHtml(neo.reason || "")
      : escapeHtml(String(neo.ms)) +
        " ms" +
        (neo.error ? " — " + escapeHtml(neo.error) : "");
    rows.push(
      "<tr><td class=\"font-medium\">Neo4j</td><td>" +
        neoCell +
        '</td><td class="monitoring-mono monitoring-cell-detail">' +
        neoDetail +
        "</td></tr>"
    );

    var mongo = m.mongo_atlas || {};
    var mongoCell;
    if (mongo.skipped) {
      mongoCell = '<span class="badge badge-warning">跳过</span>';
    } else if (mongo.ok) {
      mongoCell = '<span class="badge badge-success">正常</span>';
    } else {
      mongoCell = '<span class="badge badge-error">异常</span>';
    }
    var mongoDetail = mongo.skipped
      ? escapeHtml(mongo.reason || "")
      : escapeHtml(String(mongo.ms)) +
        " ms" +
        (mongo.db ? " — db=" + escapeHtml(mongo.db) : "") +
        (mongo.error ? " — " + escapeHtml(mongo.error) : "");
    rows.push(
      "<tr><td class=\"font-medium\">MongoDB Atlas（知识向量）</td><td>" +
        mongoCell +
        '</td><td class="monitoring-mono monitoring-cell-detail">' +
        mongoDetail +
        "</td></tr>"
    );

    if (m.mail_tcp && !m.mail_tcp.skipped) {
      var mt = m.mail_tcp;
      rows.push(
        '<tr><td class="font-medium">邮件 TCP（本机 ' +
          escapeHtml(mt.host || "") +
          '）</td><td><span class="text-sm monitoring-cell-detail">SMTP 25: ' +
          (mt.smtp_25
            ? '<span class="text-green-600">开</span>'
            : '<span class="text-red-600">不可达</span>') +
          '</span> <span class="text-sm monitoring-cell-detail ml-2">IMAP 143: ' +
          (mt.imap_143
            ? '<span class="text-green-600">开</span>'
            : '<span class="text-red-600">不可达</span>') +
          '</span></td><td class="text-sm monitoring-cell-detail">需单独进程 <code class="monitoring-inline-code">start_mail_server</code></td></tr>'
      );
    }

    mount.innerHTML =
      '<div class="card overflow-hidden"><table class="data-table w-full text-sm"><thead><tr><th>检查项</th><th>结果</th><th>耗时 / 说明</th></tr></thead><tbody>' +
      rows.join("") +
      "</tbody></table></div>";
  }

  function renderApps(m, appsConfig, mount) {
    var probes = m.http_probes || {};
    var adb = m.app_db_status || {};
    var cards = appsConfig.map(function (app) {
      var hpKey = app.httpProbeKey;
      var hp = hpKey ? probes[hpKey] : null;
      var row = adb[app.key] || {};
      var dbHtml = "";
      if (app.enabled && row.enabled) {
        dbHtml =
          '<div class="flex flex-wrap gap-x-2 gap-y-1"><dt class="text-gray-500 shrink-0">MySQL</dt><dd class="text-gray-600 min-w-0">' +
          (row.db_ok
            ? '<span class="text-green-700"><code class="monitoring-inline-code">' +
              escapeHtml(row.db_alias || "") +
              "</code> 可达</span>"
            : '<span class="text-red-600"><code class="monitoring-inline-code">' +
              escapeHtml(row.db_alias || "") +
              "</code> 异常</span>") +
          "</dd></div>";
      }
      var btn;
      if (!app.enabled) {
        btn = '<button type="button" class="btn btn-outline btn-sm w-full" disabled>未启用</button>';
      } else if (app.href) {
        btn =
          '<a href="' +
          escapeHtml(app.href) +
          '" class="btn btn-primary btn-sm w-full">进入管理</a>';
      } else {
        btn = '<button type="button" class="btn btn-outline btn-sm w-full" disabled>未配置入口</button>';
      }

      return (
        '<div class="card ' +
        (app.enabled ? "" : "opacity-60") +
        '"><div class="card-body">' +
        '<div class="flex items-start gap-3 mb-3">' +
        '<div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center shrink-0">' +
        iconSvg(app.icon) +
        "</div>" +
        '<div class="min-w-0 flex-1">' +
        '<h3 class="text-base font-semibold text-gray-800">' +
        escapeHtml(app.name) +
        "</h3>" +
        (app.enabled
          ? '<span class="badge badge-success">已启用</span>'
          : '<span class="badge badge-warning">未启用</span>') +
        "</div></div>" +
        '<dl class="space-y-2 text-sm mb-3">' +
        '<div class="flex flex-wrap gap-x-2 gap-y-1"><dt class="text-gray-500 shrink-0">HTTP</dt><dd class="text-gray-600 min-w-0">' +
        httpProbeRow(hp) +
        "</dd></div>" +
        dbHtml +
        "</dl>" +
        '<p class="text-gray-600 text-xs mb-3">' +
        escapeHtml(app.description) +
        "</p>" +
        btn +
        "</div></div>"
      );
    });
    mount.innerHTML =
      '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">' +
      cards.join("") +
      "</div>";
  }

  function renderOther(m, mount) {
    var parts = [];
    var am = m.aibroker_metrics;
    if (am) {
      parts.push('<div class="mb-8">');
      parts.push(
        '<h3 class="text-lg font-semibold text-gray-800 mb-3">AIBroker 调用指标（服务端窗口）</h3>'
      );
      parts.push('<div class="card card-body text-sm">');
      if (am.data_json) {
        parts.push(
          '<pre class="console-readonly-block monitoring-pre p-3 rounded text-xs overflow-x-auto font-mono">' +
            escapeHtml(am.data_json) +
            "</pre>"
        );
        parts.push(
          '<p class="text-xs text-gray-500 mt-2">由 <code class="monitoring-inline-code">CONSOLE_AIBROKER_ACCESS_KEY</code> 拉取 <code class="monitoring-inline-code">summary_since</code> 结果。</p>'
        );
      } else if (am.error) {
        parts.push('<p class="text-red-600">' + escapeHtml(am.error) + "</p>");
      }
      parts.push("</div></div>");
    }

    var sb = m.searchrec_backends || {};
    parts.push("<div class=\"mb-8\">");
    parts.push(
      '<h3 class="text-lg font-semibold text-gray-800 mb-2">SearchRec 检索后端（配置开关）</h3>'
    );
    parts.push(
      '<p class="text-xs text-gray-500 mb-3">以下仅反映环境变量；<code class="monitoring-inline-code">/api/searchrec/health</code> 不验证远端 OpenSearch/Milvus 等连通性。</p>'
    );
    parts.push('<div class="flex flex-wrap gap-2 text-sm">');
    [
      ["opensearch_enabled", "OpenSearch"],
      ["milvus_enabled", "Milvus"],
      ["qdrant_enabled", "Qdrant"],
      ["feast_enabled", "Feast"],
    ].forEach(function (pair) {
      var en = sb[pair[0]];
      parts.push(
        '<span class="badge ' +
          (en ? "badge-success" : "badge-neutral") +
          '">' +
          pair[1] +
          "</span>"
      );
    });
    parts.push(
      '<span class="text-gray-500 text-sm self-center">HTTP 超时: ' +
        escapeHtml(String(sb.http_timeout_s != null ? sb.http_timeout_s : "")) +
        "s</span>"
    );
    parts.push("</div></div>");

    parts.push("<div>");
    parts.push('<h3 class="text-lg font-semibold text-gray-800 mb-2">JSON 导出</h3>');
    parts.push(
      '<p class="text-sm text-gray-600">配置环境变量 <code class="monitoring-inline-code">CONSOLE_MONITORING_JSON_TOKEN</code> 后，可请求 <code class="monitoring-inline-code">/console/api/monitoring.json?token=…</code> 或请求头 <code class="monitoring-inline-code">X-Console-Monitoring-Token</code>。</p>'
    );
    parts.push("</div>");

    mount.innerHTML = parts.join("");
  }

  function setTabUi(tab) {
    document.querySelectorAll("[data-monitoring-tab]").forEach(function (btn) {
      var on = btn.getAttribute("data-monitoring-tab") === tab;
      btn.classList.toggle("is-active", on);
      btn.classList.toggle("is-inactive", !on);
    });
    document.querySelectorAll("[data-monitoring-panel]").forEach(function (p) {
      var on = p.getAttribute("data-monitoring-panel") === tab;
      p.classList.toggle("hidden", !on);
    });
  }

  function init() {
    var root = document.getElementById("monitoring-root");
    if (!root) return;

    var snapshotUrl = root.getAttribute("data-snapshot-url");
    var refreshMs = parseInt(root.getAttribute("data-refresh-ms") || "0", 10) || 0;
    var djangoVersion = root.getAttribute("data-django-version") || "";

    var cfgEl = document.getElementById("monitoring-apps-config");
    var appsConfig = [];
    try {
      appsConfig = JSON.parse(cfgEl ? cfgEl.textContent : "[]");
    } catch (e) {
      appsConfig = [];
    }

    var mountInfra = document.getElementById("monitoring-mount-infra");
    var mountApps = document.getElementById("monitoring-mount-apps");
    var mountOther = document.getElementById("monitoring-mount-other");
    var elCollected = document.getElementById("monitoring-meta-collected");
    var elStatus = document.getElementById("monitoring-meta-status");
    var elDjango = document.getElementById("monitoring-meta-django");
    if (elDjango) elDjango.textContent = "Django " + djangoVersion;

    var firstLoad = true;

    function setStatus(text) {
      if (elStatus) elStatus.textContent = text;
    }

    function applySnapshot(m) {
      if (elCollected) elCollected.textContent = m.collected_at || "—";
      if (mountInfra) renderInfra(m, mountInfra);
      if (mountApps) renderApps(m, appsConfig, mountApps);
      if (mountOther) renderOther(m, mountOther);
    }

    function fetchSnapshot() {
      if (!snapshotUrl) {
        setStatus("未配置快照地址");
        return;
      }
      setStatus(firstLoad ? "加载中…" : "刷新中…");
      fetch(snapshotUrl, { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (m) {
          applySnapshot(m);
          setStatus("已更新");
          firstLoad = false;
        })
        .catch(function (err) {
          setStatus("加载失败: " + (err.message || String(err)));
          if (elCollected) elCollected.textContent = "—";
        });
    }

    document.querySelectorAll("[data-monitoring-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setTabUi(btn.getAttribute("data-monitoring-tab"));
      });
    });

    setTabUi("apps");
    fetchSnapshot();
    if (refreshMs > 0) {
      setInterval(fetchSnapshot, refreshMs);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
