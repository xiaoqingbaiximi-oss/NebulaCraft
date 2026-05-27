var Cloud = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['☁️ 云端'] = { icon: '☁️', desc: '远程访问/云端模型/更新', keywords: '云端 远程 更新' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].push('☁️ 云端');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '☁️ 云端') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';

    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>☁️ 云端管理</h3>' + closeBtn + '</div>' +
      '<div class="result-content">' +
      '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">' +
      '<button class="btn-sm primary" onclick="Cloud._checkUpdate()" style="padding:16px;text-align:center">🆕<br>检查更新</button>' +
      '<button class="btn-sm" onclick="Cloud._cloudStatus()" style="padding:16px;text-align:center">🤖<br>云端模型</button>' +
      '<button class="btn-sm" onclick="Cloud._tunnelStatus()" style="padding:16px;text-align:center">🌐<br>远程访问</button>' +
      '</div><div id="cloud-output"></div></div></div>';
  },

  _checkUpdate: function() {
    var out = document.getElementById('cloud-output');
    if (!out) return;
    out.innerHTML = '<p style="color:var(--text2)">⏳ 检查更新...</p>';

    fetch('/api/update', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}', signal:AbortSignal.timeout(10000) })
      .then(function(r){return r.json();}).then(function(d){
        if (!out) return;
        if (!d.ok) { out.innerHTML = '<p style="color:var(--danger)">检查失败</p>'; return; }
        var html = '<h4>🆕 版本信息</h4>';
        html += '<p>当前: <strong>v' + d.current + '</strong></p>';
        html += '<p>最新: <strong>v' + d.latest + '</strong></p>';
        if (d.update_available) {
          html += '<p style="color:var(--success)">🎉 有新版本可用!</p>';
          if (d.update_url) html += '<p><a href="' + d.update_url + '" target="_blank" style="color:var(--accent)">下载更新</a></p>';
          if (d.update_notes) html += '<pre style="background:var(--bg);padding:12px;border-radius:8px;font-size:.85rem;max-height:200px;overflow-y:auto">' + d.update_notes + '</pre>';
        } else {
          html += '<p style="color:var(--text2)">✅ 已是最新版本</p>';
        }
        out.innerHTML = html;
      });
  },

  _cloudStatus: function() {
    var out = document.getElementById('cloud-output');
    if (!out) return;
    out.innerHTML = '<p style="color:var(--text2)">⏳ 检测云端模型...</p>';

    fetch('/api/cloud', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}', signal:AbortSignal.timeout(5000) })
      .then(function(r){return r.json();}).then(function(d){
        if (!out) return;
        if (!d.ok) { out.innerHTML = '<p style="color:var(--danger)">检测失败</p>'; return; }
        var html = '<h4>🤖 云端模型</h4>';
        html += '<p style="font-size:.8rem;color:var(--text2);margin-bottom:12px">状态: ' + (d.enabled ? '🟢 可用' : '⚪ 未配置') + '</p>';
        if (d.providers) {
          Object.keys(d.providers).forEach(function(k) {
            var v = d.providers[k];
            html += '<div style="display:flex;justify-content:space-between;padding:8px;background:var(--bg);border-radius:6px;margin-bottom:4px"><span>' + k + '</span><span style="font-size:.8rem">' + (v.available ? '🟢 ' + v.model : '⚪ 需配置') + '</span></div>';
          });
        }
        html += '<p style="font-size:.7rem;color:var(--text2);margin-top:12px">设置环境变量: OPENAI_API_KEY / DEEPSEEK_API_KEY / GROQ_API_KEY</p>';
        out.innerHTML = html;
      });
  },

  _tunnelStatus: function() {
    var out = document.getElementById('cloud-output');
    if (!out) return;
    out.innerHTML = '<p style="color:var(--text2)">⏳ 检测隧道...</p>';

    fetch('/api/tunnel', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'status'}), signal:AbortSignal.timeout(5000) })
      .then(function(r){return r.json();}).then(function(d){
        if (!out) return;
        if (!d.ok) { out.innerHTML = '<p style="color:var(--danger)">检测失败</p>'; return; }
        var html = '<h4>🌐 远程访问</h4>';
        if (d.active && d.url) {
          html += '<p style="color:var(--success)">🟢 公网可用</p>';
          html += '<p>地址: <a href="' + d.url + '" target="_blank" style="color:var(--accent)">' + d.url + '</a></p>';
        } else {
          html += '<p style="color:var(--text2)">⚪ 未启用</p>';
          html += '<p style="font-size:.8rem;color:var(--text2)">安装 ngrok 后可使用公网访问</p>';
          html += '<p><a href="https://ngrok.com/download" target="_blank" style="color:var(--accent);font-size:.8rem">下载 ngrok</a></p>';
        }
        html += '<p style="font-size:.7rem;color:var(--text2);margin-top:8px">' + (d.tips || '') + '</p>';
        out.innerHTML = html;
      });
  }
};