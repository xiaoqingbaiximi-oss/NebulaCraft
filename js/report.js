var Report = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['📋 报告'] = { icon: '📋', desc: '使用统计周报/月报', keywords: '报告 周报 月报 统计' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].push('📋 报告');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '📋 报告') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';

    var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
    var total = history.length;
    var now = new Date();
    var weekAgo = new Date(now - 7 * 86400000);
    var monthAgo = new Date(now - 30 * 86400000);

    var weekMsgs = history.filter(function(h) { return new Date(h.time) > weekAgo; }).length;
    var monthMsgs = history.filter(function(h) { return new Date(h.time) > monthAgo; }).length;
    var sessions = new Set(history.map(function(h) { return h.sessionId; })).size;

    var habits = JSON.parse(localStorage.getItem('nh') || '[]');
    var today = now.toISOString().split('T')[0];
    var habitDone = habits.filter(function(h) { return (h.d || []).indexOf(today) !== -1; }).length;

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📋 健康报告</h3>' + closeBtn + '</div><div class="result-content">';
    html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px">';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:1.8rem;font-weight:700;color:var(--accent)">' + weekMsgs + '</div><div style="font-size:.75rem;color:var(--text2)">本周消息</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:1.8rem;font-weight:700;color:var(--success)">' + monthMsgs + '</div><div style="font-size:.75rem;color:var(--text2)">本月消息</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:1.8rem;font-weight:700;color:var(--warning)">' + sessions + '</div><div style="font-size:.75rem;color:var(--text2)">会话数</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:1.8rem;font-weight:700;color:var(--accent2)">' + habitDone + '/' + habits.length + '</div><div style="font-size:.75rem;color:var(--text2)">今日打卡</div></div>';
    html += '</div>';

    html += '<h4>💡 建议</h4><ul style="color:var(--text2);padding-left:20px">';
    if (weekMsgs > 50) html += '<li>本周对话活跃，考虑导出重要对话备份</li>';
    if (habits.length > 0 && habitDone < habits.length) html += '<li>还有 ' + (habits.length - habitDone) + ' 个习惯未打卡</li>';
    if (total > 500) html += '<li>历史消息较多，建议定期清理或导出</li>';
    html += '<li>继续保持学习节奏！🎯</li></ul>';

    html += '</div></div>';
    el.innerHTML = html;
  }
};