var Bookmarks = {
  list: [],

  init: function() {
    this.list = JSON.parse(localStorage.getItem('nebula_bookmarks') || '[]');
  },

  add: function() {
    var msgs = document.querySelectorAll('.msg');
    if (msgs.length === 0) { App.toast('没有对话可收藏', 'error'); return; }

    var lastMsg = msgs[msgs.length - 1];
    var content = lastMsg.querySelector('.msg-bubble').textContent.slice(0, 100);
    var role = lastMsg.classList.contains('user') ? '用户' : 'AI';
    var time = new Date().toLocaleString('zh-CN');

    this.list.push({
      id: Date.now(),
      role: role,
      preview: content,
      time: time,
      sessionId: Chat.sessionId,
    });

    if (this.list.length > 50) this.list.shift();
    localStorage.setItem('nebula_bookmarks', JSON.stringify(this.list));
    App.toast('已收藏对话', 'success');
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>🔖 对话书签</h3>' + closeBtn + '</div><div class="result-content">';

    if (this.list.length === 0) {
      html += '<p style="color:var(--text2);text-align:center;padding:20px">暂无书签，在对话中点收藏添加</p>';
    } else {
      this.list.reverse().forEach(function(b, i) {
        html += '<div style="padding:12px;background:var(--bg);border-radius:8px;margin-bottom:6px;cursor:pointer" onclick="Bookmarks._jump(' + i + ')">' +
          '<div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="font-size:.8rem;color:var(--accent)">' + b.role + '</span><span style="font-size:.75rem;color:var(--text2)">' + b.time + '</span></div>' +
          '<p style="font-size:.9rem">' + self._esc(b.preview) + '</p></div>';
      });
    }

    html += '</div></div>';
    el.innerHTML = html;
  },

  _jump: function(i) { App.toast('书签 #' + (this.list.length - i), 'info'); },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = (s || ''); return d.innerHTML; }
};