var Templates = {
  list: [],

  init: function() {
    this.list = JSON.parse(localStorage.getItem('nebula_templates') || '[]');
    if (this.list.length === 0) {
      this.list = [
        { name: '润色文章', prompt: '润色：' },
        { name: '翻译英文', prompt: '翻译：' },
        { name: '写周报', prompt: '帮我写一份本周工作周报，包含：完成事项、遇到的问题、下周计划' },
        { name: '代码审查', prompt: '代码审查：' },
        { name: '头脑风暴', prompt: '针对以下主题进行头脑风暴，列出10个创意点子：' },
      ];
      this.save();
    }
  },

  save: function() {
    localStorage.setItem('nebula_templates', JSON.stringify(this.list));
  },

  showPanel: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📋 对话模板</h3>' + closeBtn + '</div><div class="result-content">';

    this.list.forEach(function(t, i) {
      html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg);border-radius:8px;margin-bottom:6px;cursor:pointer" onclick="Templates.use(' + i + ')">' +
        '<div><strong>' + self._esc(t.name) + '</strong><p style="font-size:.8rem;color:var(--text2)">' + self._esc(t.prompt.slice(0, 80)) + '</p></div>' +
        '<button class="btn-sm" onclick="event.stopPropagation();Templates.delete(' + i + ')">🗑️</button></div>';
    });

    html += '</div><div class="result-actions" style="margin-top:12px;flex-wrap:wrap;gap:6px">' +
      '<input id="tpl-name" placeholder="模板名称" style="flex:1;min-width:80px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<input id="tpl-prompt" placeholder="模板内容" style="flex:2;min-width:120px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<button class="btn-sm primary" onclick="Templates.add()">➕ 添加</button></div></div>';

    el.innerHTML = html;
  },

  use: function(i) {
    var t = this.list[i];
    if (t) {
      var input = document.getElementById('chat-input');
      if (input) { input.value = t.prompt; input.focus(); Chat.autoResize(); }
      UI.switchView('chat');
    }
  },

  add: function() {
    var name = document.getElementById('tpl-name').value.trim();
    var prompt = document.getElementById('tpl-prompt').value.trim();
    if (!name || !prompt) return;
    this.list.push({ name: name, prompt: prompt });
    this.save();
    this.showPanel();
    App.toast('模板已添加', 'success');
  },

  delete: function(i) {
    this.list.splice(i, 1);
    this.save();
    this.showPanel();
  },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
};