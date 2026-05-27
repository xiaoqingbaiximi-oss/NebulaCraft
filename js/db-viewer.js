var Snippets = {
  list: [],

  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['📋 代码片段'] = { icon: '📋', desc: '保存/搜索代码片段', keywords: '代码 片段 snippet' };
    if (!Tools.categories['🔧 开发']) Tools.categories['🔧 开发'] = [];
    Tools.categories['🔧 开发'].push('📋 代码片段');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '📋 代码片段') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };

    this.list = JSON.parse(localStorage.getItem('nebula_snippets') || '[]');
  },

  show: function(filter) {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    var filtered = filter ? this.list.filter(function(s) {
      return (s.title + s.code + s.lang + (s.tags || []).join(' ')).toLowerCase().indexOf(filter.toLowerCase()) !== -1;
    }) : this.list;

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📋 代码片段库</h3>' + closeBtn + '</div><div class="result-content">' +
      '<input id="snippet-search" placeholder="🔍 搜索片段..." value="' + (filter || '') + '" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit;margin-bottom:12px;box-sizing:border-box" oninput="Snippets.show(this.value)">';

    if (filtered.length === 0) {
      html += '<p style="color:var(--text2);text-align:center;padding:20px">' + (filter ? '未找到匹配片段' : '暂无片段，添加一个吧') + '</p>';
    } else {
      filtered.forEach(function(s, i) {
        html += '<div style="padding:12px;background:var(--bg);border-radius:8px;margin-bottom:8px">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">' +
          '<strong>' + self._esc(s.title) + '</strong>' +
          '<span style="font-size:.75rem;color:var(--accent)">' + self._esc(s.lang || '') + '</span></div>' +
          '<pre style="background:#1a1a35;padding:10px;border-radius:6px;font-family:monospace;font-size:.8rem;max-height:200px;overflow-y:auto;white-space:pre-wrap;cursor:pointer" onclick="Snippets._copy(\'' + i + '\')">' + self._esc(s.code.slice(0, 500)) + '</pre>' +
          '<div style="display:flex;gap:4px;margin-top:6px">' +
          (s.tags || []).map(function(t) { return '<span style="background:var(--accent-glow);padding:2px 8px;border-radius:10px;font-size:.7rem">' + t + '</span>'; }).join('') +
          '</div>' +
          '<button class="btn-sm" onclick="Snippets._delete(' + i + ')" style="margin-top:6px">🗑️</button></div>';
      });
    }

    html += '<div class="result-actions" style="margin-top:12px;flex-wrap:wrap;gap:6px">' +
      '<input id="snip-title" placeholder="标题" style="flex:1;min-width:80px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<input id="snip-lang" placeholder="语言" style="flex:1;min-width:60px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<input id="snip-tags" placeholder="标签,逗号分隔" style="flex:1;min-width:80px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<textarea id="snip-code" rows="4" placeholder="代码内容" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;box-sizing:border-box;font-size:.85rem"></textarea>' +
      '<button class="btn-sm primary" onclick="Snippets._add()">➕ 添加</button></div></div>';

    el.innerHTML = html;
  },

  _add: function() {
    var title = document.getElementById('snip-title').value.trim();
    var code = document.getElementById('snip-code').value.trim();
    var lang = document.getElementById('snip-lang').value.trim();
    var tags = document.getElementById('snip-tags').value.split(',').map(function(t) { return t.trim(); }).filter(Boolean);

    if (!title || !code) { App.toast('标题和代码不能为空', 'error'); return; }

    this.list.push({ title: title, code: code, lang: lang, tags: tags, time: new Date().toLocaleString('zh-CN') });
    if (this.list.length > 100) this.list.shift();
    localStorage.setItem('nebula_snippets', JSON.stringify(this.list));
    this.show();
    App.toast('片段已保存', 'success');
  },

  _copy: function(i) {
    var code = this.list[i] ? this.list[i].code : '';
    if (code) { navigator.clipboard.writeText(code); App.toast('已复制', 'success'); }
  },

  _delete: function(i) { this.list.splice(i, 1); localStorage.setItem('nebula_snippets', JSON.stringify(this.list)); this.show(); },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = (s || ''); return d.innerHTML; }
};