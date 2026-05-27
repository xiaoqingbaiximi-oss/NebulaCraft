var Tagger = {
  rules: {
    '技术': ['代码', 'bug', 'API', '函数', 'Python', 'JS', 'SQL', '部署', 'Docker'],
    '写作': ['文章', '润色', '改稿', '文案', '小说', '故事', '写', '编辑'],
    '学习': ['问题', '解释', '定义', '教程', '学习', '如何', '什么是'],
    '生活': ['天气', '食谱', '菜', '旅游', '穿搭', '健康', '运动'],
    '工作': ['简历', '面试', '周报', '会议', '项目', '任务', '计划'],
    '创意': ['设计', '配色', '灵感', '创意', '头脑风暴', '想法', '海报'],
  },

  init: function() {},

  analyze: function(text) {
    var tags = [];
    var lower = (text || '').toLowerCase();
    var self = this;
    Object.keys(this.rules).forEach(function(cat) {
      var matched = self.rules[cat].some(function(kw) {
        return lower.indexOf(kw.toLowerCase()) !== -1;
      });
      if (matched) tags.push(cat);
    });
    return tags.length > 0 ? tags : ['其他'];
  },

  autoTag: function(text) {
    var tags = this.analyze(text);
    return { text: (text||'').slice(0, 100), tags: tags, primary: tags[0] };
  },

  showPanel: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';
    var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
    var userMsgs = history.filter(function(h) { return h.role === 'user'; }).slice(-50);
    var tagStats = {};
    var self = this;
    userMsgs.forEach(function(h) {
      var tags = self.analyze(h.content || '');
      tags.forEach(function(t) { tagStats[t] = (tagStats[t] || 0) + 1; });
    });
    var total = userMsgs.length;
    var sortedTags = Object.entries(tagStats).sort(function(a, b) { return b[1] - a[1]; });
    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>🏷️ 智能标签</h3>' + closeBtn + '</div><div class="result-content">';
    html += '<p style="color:var(--text2);margin-bottom:12px">分析最近 ' + total + ' 条消息</p>';
    sortedTags.forEach(function(t) {
      var pct = Math.round(t[1] / total * 100);
      var color = pct > 30 ? 'var(--accent)' : pct > 15 ? 'var(--accent2)' : 'var(--text2)';
      html += '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:.85rem"><span>' + t[0] + '</span><span>' + t[1] + ' (' + pct + '%)</span></div>';
      html += '<div style="height:6px;background:var(--bg);border-radius:3px;margin-top:4px"><div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:3px"></div></div></div>';
    });
    html += '</div></div>';
    el.innerHTML = html;
  },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; }
};