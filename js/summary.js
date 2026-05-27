var Summary = {
  init: function() {
    // 每天首次打开自动生成昨日摘要
    this._dailySummary();
  },

  _dailySummary: function() {
    var today = new Date().toDateString();
    var lastSummary = localStorage.getItem('nebula_last_summary_date');

    if (lastSummary === today) return;

    var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
    var yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    var yesterdayStr = yesterday.toISOString().split('T')[0];

    var yesterdayMsgs = history.filter(function(h) {
      return (h.time || '').startsWith(yesterdayStr);
    });

    if (yesterdayMsgs.length === 0) {
      localStorage.setItem('nebula_last_summary_date', today);
      return;
    }

    // 延迟执行，等页面加载完
    setTimeout(function() {
      var userMsgs = yesterdayMsgs.filter(function(h) { return h.role === 'user'; });
      var topics = userMsgs.slice(0, 10).map(function(h) { return (h.content || '').slice(0, 60); });

      var summary = {
        date: yesterdayStr,
        total: yesterdayMsgs.length,
        topics: topics,
        generated: new Date().toISOString(),
      };

      var summaries = JSON.parse(localStorage.getItem('nebula_summaries') || '[]');
      summaries.unshift(summary);
      if (summaries.length > 30) summaries.pop();
      localStorage.setItem('nebula_summaries', JSON.stringify(summaries));
      localStorage.setItem('nebula_last_summary_date', today);

      // Toast 通知
      if (typeof App !== 'undefined') {
        App.toast('📊 昨日对话 ' + yesterdayMsgs.length + ' 条消息', 'info', 5000);
      }
    }, 5000);
  },

  showPanel: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var self = this;

    var summaries = JSON.parse(localStorage.getItem('nebula_summaries') || '[]');

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📊 对话摘要</h3>' + closeBtn + '</div><div class="result-content">';

    if (summaries.length === 0) {
      html += '<p style="color:var(--text2);text-align:center;padding:20px">暂无摘要，明天来看看</p>';
    } else {
      summaries.slice(0, 14).forEach(function(s) {
        html += '<div style="padding:12px;background:var(--bg);border-radius:8px;margin-bottom:8px">';
        html += '<div style="display:flex;justify-content:space-between;margin-bottom:6px"><strong>📅 ' + s.date + '</strong><span style="font-size:.8rem;color:var(--text2)">' + s.total + ' 条消息</span></div>';
        if (s.topics && s.topics.length > 0) {
          html += '<div style="display:flex;flex-wrap:wrap;gap:4px">';
          s.topics.forEach(function(t) {
            html += '<span style="background:var(--accent-glow);padding:2px 8px;border-radius:10px;font-size:.75rem">' + self._esc(t) + '</span>';
          });
          html += '</div>';
        }
        html += '</div>';
      });
    }

    html += '</div></div>';
    el.innerHTML = html;
  },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
};