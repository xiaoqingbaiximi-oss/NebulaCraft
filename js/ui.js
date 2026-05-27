var UI = {
  currentView: 'chat',
  sidebarOpen: false,

  init: function() {
    this.bindSidebar();
    this.bindViewSwitching();
    this.handleResize();
    var lastView = localStorage.getItem('nebula_last_view') || 'chat';
    this.switchView(lastView);
  },

  bindSidebar: function() {
    var overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
      overlay.addEventListener('click', function() { UI.closeSidebar(); });
    }
  },

  toggleSidebar: function() {
    if (this.sidebarOpen) { this.closeSidebar(); } else { this.openSidebar(); }
  },

  openSidebar: function() {
    this.sidebarOpen = true;
    var s = document.getElementById('sidebar');
    var o = document.getElementById('sidebar-overlay');
    if (s) s.classList.add('open');
    if (o) o.classList.add('show');
  },

  closeSidebar: function() {
    this.sidebarOpen = false;
    var s = document.getElementById('sidebar');
    var o = document.getElementById('sidebar-overlay');
    if (s) s.classList.remove('open');
    if (o) o.classList.remove('show');
  },

  bindViewSwitching: function() {
    var self = this;
    document.querySelectorAll('.nav-item[data-view]').forEach(function(item) {
      item.addEventListener('click', function() {
        self.switchView(this.dataset.view);
        self.closeSidebar();
      });
    });
    document.querySelectorAll('.bottom-nav-item[data-view]').forEach(function(item) {
      item.addEventListener('click', function() {
        self.switchView(this.dataset.view);
      });
    });
  },

  switchView: function(view) {
    this.currentView = view;
    document.querySelectorAll('.view').forEach(function(v) { v.classList.remove('active'); });
    var target = document.getElementById('view-' + view);
    if (target) target.classList.add('active');
    document.querySelectorAll('.nav-item[data-view]').forEach(function(item) {
      item.classList.toggle('active', item.dataset.view === view);
    });
    document.querySelectorAll('.bottom-nav-item[data-view]').forEach(function(item) {
      item.classList.toggle('active', item.dataset.view === view);
    });
    if (view === 'chat') { var inp = document.getElementById('chat-input'); if (inp) inp.focus(); }
    if (view === 'tools') { var s = document.getElementById('tool-search'); if (s) s.focus(); }
    if (view === 'history') { this.loadHistoryView(); }
    localStorage.setItem('nebula_last_view', view);
  },

  loadHistoryView: function() {
    var container = document.getElementById('history-list');
    if (!container) return;
    try {
      var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
      if (history.length === 0) { container.innerHTML = '<div class="empty-state">📋 还没有对话记录</div>'; return; }
      var sessions = {};
      history.forEach(function(h) {
        var sid = h.sessionId || 'default';
        if (!sessions[sid]) sessions[sid] = [];
        sessions[sid].push(h);
      });
      var html = '';
      Object.entries(sessions).reverse().forEach(function(entry) {
        var msgs = entry[1];
        var first = msgs[0];
        var time = first.time ? new Date(first.time).toLocaleString('zh-CN') : '';
        var preview = (first.content || '').slice(0, 80);
        html += '<div class="history-session" onclick="UI.loadSession(\'' + entry[0] + '\')" style="padding:12px;background:var(--surface);border-radius:8px;margin-bottom:8px;cursor:pointer">';
        html += '<div style="display:flex;justify-content:space-between;font-size:.8rem;color:var(--text2)"><span>' + time + '</span><span>' + msgs.length + ' 条</span></div>';
        html += '<div style="margin-top:4px">' + preview + '</div></div>';
      });
      container.innerHTML = html;
    } catch(e) { container.innerHTML = '<div class="empty-state">⚠️ 加载失败</div>'; }
  },

  loadSession: function(sid) {
    try {
      var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
      var msgs = history.filter(function(h) { return h.sessionId === sid; });
      var container = document.getElementById('messages');
      if (!container) return;
      container.innerHTML = '';
      msgs.forEach(function(h) {
        if (typeof Chat !== 'undefined') Chat.addMessage(h.role, h.content);
      });
      this.switchView('chat');
      App.toast('已加载 ' + msgs.length + ' 条消息', 'info');
    } catch(e) { App.toast('加载失败', 'error'); }
  },

  handleResize: function() {
    window.addEventListener('resize', function() {
      if (window.innerWidth < 768 && UI.sidebarOpen) UI.closeSidebar();
    });
  }
};