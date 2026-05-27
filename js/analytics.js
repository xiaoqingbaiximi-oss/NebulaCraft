var Analytics = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['📈 统计'] = { icon: '📈', desc: '对话数据分析', keywords: '统计 分析 数据' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].push('📈 统计');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '📈 统计') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';

    var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
    var total = history.length;
    var userMsgs = history.filter(function(h) { return h.role === 'user'; }).length;
    var aiMsgs = history.filter(function(h) { return h.role === 'ai'; }).length;

    // 按日期分组
    var byDate = {};
    history.forEach(function(h) {
      var d = (h.time || '').slice(0, 10);
      if (d) byDate[d] = (byDate[d] || 0) + 1;
    });
    var dates = Object.keys(byDate).sort().reverse();
    var recentDays = dates.slice(0, 7);

    // 热门词
    var words = {};
    history.filter(function(h) { return h.role === 'user'; }).forEach(function(h) {
      (h.content || '').split(/\s+/).forEach(function(w) {
        if (w.length >= 2) words[w] = (words[w] || 0) + 1;
      });
    });
    var topWords = Object.entries(words).sort(function(a, b) { return b[1] - a[1]; }).slice(0, 10);

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📈 对话统计</h3>' + closeBtn + '</div><div class="result-content">';

    html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px">';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--accent)">' + total + '</div><div style="font-size:.75rem;color:var(--text2)">总消息</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--success)">' + userMsgs + '</div><div style="font-size:.75rem;color:var(--text2)">用户消息</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--accent2)">' + aiMsgs + '</div><div style="font-size:.75rem;color:var(--text2)">AI 回复</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--warning)">' + dates.length + '</div><div style="font-size:.75rem;color:var(--text2)">活跃天数</div></div>';
    html += '</div>';

    if (recentDays.length > 0) {
      html += '<h4 style="margin-bottom:8px">📅 最近7天</h4><div style="display:flex;align-items:flex-end;gap:8px;height:100px;margin-bottom:16px">';
      var maxCount = Math.max.apply(null, recentDays.map(function(d) { return byDate[d] || 0; }));
      recentDays.reverse().forEach(function(d) {
        var count = byDate[d] || 0;
        var h = maxCount > 0 ? Math.max(4, (count / maxCount) * 80) : 4;
        html += '<div style="flex:1;text-align:center"><div style="height:' + h + 'px;background:var(--accent);border-radius:4px 4px 0 0;transition:height 0.5s"></div><div style="font-size:.6rem;color:var(--text2);margin-top:4px">' + d.slice(5) + '</div><div style="font-size:.65rem">' + count + '</div></div>';
      });
      html += '</div>';
    }

    if (topWords.length > 0) {
      html += '<h4 style="margin-bottom:8px">🔤 高频词</h4><div style="display:flex;flex-wrap:wrap;gap:6px">';
      topWords.forEach(function(w) {
        html += '<span style="background:var(--accent-glow);padding:4px 12px;border-radius:14px;font-size:.8rem">' + w[0] + ' <span style="color:var(--text2)">' + w[1] + '</span></span>';
      });
      html += '</div>';
    }

    html += '</div></div>';
    el.innerHTML = html;
  }
};