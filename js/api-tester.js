var APITester = {
  history: [],

  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['🔧 API测试'] = { icon: '🔧', desc: '内置API调试工具', keywords: 'API 测试 调试 Postman' };
    if (!Tools.categories['🔧 开发']) Tools.categories['🔧 开发'] = [];
    Tools.categories['🔧 开发'].push('🔧 API测试');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '🔧 API测试') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };

    this.history = JSON.parse(localStorage.getItem('api_tester_history') || '[]');
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    var endpoints = [
      '/api/chat', '/api/calculator', '/api/generator', '/api/translate',
      '/api/smart', '/api/extra', '/api/knowledge', '/api/agent',
      '/api/sd_image', '/api/plugin', '/api/export', '/health'
    ];

    var historyHtml = '';
    if (this.history.length > 0) {
      historyHtml = '<h4 style="margin-top:12px">📋 历史</h4>';
      this.history.slice(-5).reverse().forEach(function(h) {
        historyHtml += '<div style="padding:6px 10px;background:var(--bg);border-radius:6px;margin-bottom:4px;font-size:.8rem;cursor:pointer" onclick="APITester._loadHistory(\'' + h.endpoint + '\',\'' + h.body.replace(/'/g,"\\'") + '\')">' +
          '<span style="color:var(--accent)">' + h.endpoint + '</span> ' + h.body.slice(0, 60) + '</div>';
      });
    }

    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>🔧 API 测试控制台</h3>' + closeBtn + '</div>' +
      '<div class="result-content">' +
      '<div style="display:flex;gap:8px;margin-bottom:8px">' +
      '<select id="api-endpoint" style="flex:1;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;font-size:.85rem">' +
      endpoints.map(function(e) { return '<option value="' + e + '">' + e + '</option>'; }).join('') + '</select>' +
      '<button class="btn-sm primary" onclick="APITester._send()">🚀 发送</button></div>' +
      '<textarea id="api-body" rows="6" placeholder=\'{"message":"你好"}\' style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;min-height:100px;box-sizing:border-box;font-size:.85rem"></textarea>' +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<button class="btn-sm" onclick="APITester._formatBody()">✨ 格式化</button>' +
      '<button class="btn-sm" onclick="APITester._clearHistory()">🗑️ 清除历史</button></div>' +
      '<div id="api-response" style="margin-top:12px"></div>' + historyHtml + '</div></div>';
  },

  _send: function() {
    var endpoint = document.getElementById('api-endpoint').value;
    var bodyStr = document.getElementById('api-body').value.trim();
    var out = document.getElementById('api-response');
    if (!out) return;

    if (!bodyStr) { App.toast('请输入请求体', 'error'); return; }

    var body;
    try { body = JSON.parse(bodyStr); } catch(e) { App.toast('JSON格式错误', 'error'); return; }

    out.innerHTML = '<p style="color:var(--text2)">⏳ 请求中...</p>';

    var self = this;
    var startTime = Date.now();

    fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000)
    }).then(function(r) { return r.json(); }).then(function(d) {
      var elapsed = Date.now() - startTime;
      out.innerHTML = '<div style="display:flex;justify-content:space-between;margin-bottom:8px">' +
        '<span style="color:var(--success)">✅ ' + r.status + ' OK</span>' +
        '<span style="font-size:.8rem;color:var(--text2)">' + elapsed + 'ms</span></div>' +
        '<pre style="background:var(--bg);padding:12px;border-radius:8px;font-family:monospace;font-size:.8rem;max-height:400px;overflow-y:auto;white-space:pre-wrap;word-break:break-word">' + JSON.stringify(d, null, 2) + '</pre>';

      self.history.push({ endpoint: endpoint, body: bodyStr, time: new Date().toLocaleString('zh-CN') });
      if (self.history.length > 20) self.history.shift();
      localStorage.setItem('api_tester_history', JSON.stringify(self.history));
    }).catch(function(e) {
      out.innerHTML = '<div style="color:var(--danger)">❌ 请求失败: ' + e.message + '</div>';
    });
  },

  _formatBody: function() {
    var ta = document.getElementById('api-body');
    try { var obj = JSON.parse(ta.value); ta.value = JSON.stringify(obj, null, 2); }
    catch(e) { App.toast('JSON格式错误', 'error'); }
  },

  _loadHistory: function(endpoint, body) {
    document.getElementById('api-endpoint').value = endpoint;
    document.getElementById('api-body').value = body;
  },

  _clearHistory: function() {
    this.history = [];
    localStorage.removeItem('api_tester_history');
    this.show();
    App.toast('历史已清除', 'info');
  }
};