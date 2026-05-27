var Enterprise = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['🏢 管理'] = { icon: '🏢', desc: '审计日志/配额/用户管理', keywords: '管理 审计 配额' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].push('🏢 管理');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '🏢 管理') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>🏢 企业管理</h3>' + closeBtn + '</div>' +
      '<div class="result-content"><p style="color:var(--text2);margin-bottom:16px">审计日志 · 使用配额 · 数据管理</p>' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">' +
      '<button class="btn-sm primary" onclick="Enterprise._audit()">📋 审计日志</button>' +
      '<button class="btn-sm" onclick="Enterprise._quota()">📊 使用配额</button>' +
      '<button class="btn-sm" onclick="Backup.exportAll()">💾 导出数据</button>' +
      '<button class="btn-sm" onclick="Backup.importAll()">📥 导入数据</button>' +
      '<button class="btn-sm" onclick="Backup.restore()">🔄 恢复备份</button>' +
      '</div><div id="enterprise-output"></div></div></div>';
  },

  _audit: function() {
    var out = document.getElementById('enterprise-output');
    if (!out) return;
    out.innerHTML = '<p style="color:var(--text2)">⏳ 加载审计日志...</p>';
    var self = this;

    fetch('/api/audit', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'stats'}), signal:AbortSignal.timeout(5000) })
      .then(function(r){return r.json();}).then(function(d){
        if (!out) return;
        if (!d.ok || !d.stats) { out.innerHTML = '<p style="color:var(--danger)">加载失败</p>'; return; }
        var s = d.stats;
        var html = '<h4 style="margin-top:12px">📋 审计概况</h4>';
        html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:12px">';
        html += '<div style="padding:12px;background:var(--bg);border-radius:8px;text-align:center"><div style="font-size:1.5rem;font-weight:700;color:var(--accent)">' + s.total + '</div><div style="font-size:.75rem;color:var(--text2)">总事件</div></div>';
        html += '<div style="padding:12px;background:var(--bg);border-radius:8px;text-align:center"><div style="font-size:1.5rem;font-weight:700;color:var(--success)">' + s.today + '</div><div style="font-size:.75rem;color:var(--text2)">今日事件</div></div>';
        html += '</div>';
        if (s.top_actions && s.top_actions.length > 0) {
          html += '<h4 style="margin-bottom:8px">高频操作</h4>';
          s.top_actions.forEach(function(a) {
            html += '<div style="display:flex;justify-content:space-between;padding:8px;background:var(--bg);border-radius:6px;margin-bottom:4px"><span>' + self._esc(a[0]) + '</span><span style="color:var(--accent)">' + a[1] + '</span></div>';
          });
        }
        out.innerHTML = html;
      }).catch(function() { if(out) out.innerHTML = '<p style="color:var(--danger)">加载失败</p>'; });
  },

  _quota: function() {
    var out = document.getElementById('enterprise-output');
    if (!out) return;
    out.innerHTML = '<p style="color:var(--text2)">⏳ 加载配额...</p>';
    var self = this;

    fetch('/api/quota', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'check'}), signal:AbortSignal.timeout(5000) })
      .then(function(r){return r.json();}).then(function(d){
        if (!out) return;
        if (!d.ok || !d.quota) { out.innerHTML = '<p style="color:var(--danger)">加载失败</p>'; return; }
        var q = d.quota;
        var html = '<h4 style="margin-top:12px">📊 使用配额</h4>';
        html += '<p style="font-size:.8rem;color:var(--text2);margin-bottom:8px">状态: ' + (q.quota_ok ? '🟢 正常' : '🔴 超限') + '</p>';
        Object.keys(q.daily).forEach(function(k) {
          var v = q.daily[k];
          var pct = v.limit > 0 ? Math.round(v.used / v.limit * 100) : 0;
          var color = pct > 80 ? 'var(--danger)' : pct > 50 ? 'var(--warning)' : 'var(--success)';
          html += '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:.85rem"><span>' + k + '</span><span>' + v.used + ' / ' + v.limit + '</span></div>';
          html += '<div style="height:6px;background:var(--bg);border-radius:3px;margin-top:4px"><div style="height:100%;width:' + Math.min(100, pct) + '%;background:' + color + ';border-radius:3px;transition:width 0.5s"></div></div></div>';
        });
        html += '<h4 style="margin-top:16px">📈 累计</h4>';
        Object.keys(q.total).forEach(function(k) {
          html += '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:.85rem"><span>' + k + '</span><span style="color:var(--accent)">' + q.total[k] + '</span></div>';
        });
        out.innerHTML = html;
      }).catch(function() { if(out) out.innerHTML = '<p style="color:var(--danger)">加载失败</p>'; });
  },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
};