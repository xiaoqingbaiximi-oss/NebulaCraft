var Dashboard = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['📊 仪表盘'] = { icon: '📊', desc: '数据总览与统计', keywords: '仪表盘 统计' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].unshift('📊 仪表盘');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '📊 仪表盘') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

showChart: function() {
  var el = document.getElementById('tools-result');
  if (!el) return;
  var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';

  var history = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]');
  var byDate = {};
  history.forEach(function(h) {
    var d = (h.time || '').slice(0, 10);
    if (d) byDate[d] = (byDate[d] || 0) + 1;
  });
  var dates = Object.keys(byDate).sort();
  var last7 = dates.slice(-7);

  el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📈 趋势图表</h3>' + closeBtn + '</div>' +
    '<div class="result-content"><canvas id="dashboardChart" style="max-height:300px"></canvas></div></div>';

  setTimeout(function() {
    var ctx = document.getElementById('dashboardChart');
    if (ctx && typeof Chart !== 'undefined') {
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: last7.map(function(d) { return d.slice(5); }),
          datasets: [{
            label: '每日消息数',
            data: last7.map(function(d) { return byDate[d] || 0; }),
            borderColor: '#6c5ce7',
            backgroundColor: 'rgba(108,92,231,0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#6c5ce7',
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { labels: { color: '#9090b8' } }
          },
          scales: {
            x: { ticks: { color: '#9090b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { ticks: { color: '#9090b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true }
          }
        }
      });
    }
  }, 300);
},

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px" title="关闭">✕</button>';

    // 获取数据
    var chatCount = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]').length;
    var noteCount = JSON.parse(localStorage.getItem('nebula_local_notes') || '[]').length;
    var habits = JSON.parse(localStorage.getItem('nh') || '[]');
    var habitTotal = habits.length;
    var today = new Date().toISOString().split('T')[0];
    var habitDone = habits.filter(function(h) { return (h.d||[]).indexOf(today) !== -1; }).length;

    var html = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📊 仪表盘</h3>' + closeBtn + '</div>';
    html += '<div class="result-content">';
    html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px">';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--accent)">' + chatCount + '</div><div style="font-size:.75rem;color:var(--text2)">消息数</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--success)">' + noteCount + '</div><div style="font-size:.75rem;color:var(--text2)">笔记</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--warning)">' + habitDone + '/' + habitTotal + '</div><div style="font-size:.75rem;color:var(--text2)">今日打卡</div></div>';
    html += '<div style="text-align:center;padding:16px;background:var(--bg);border-radius:12px"><div style="font-size:2rem;font-weight:700;color:var(--accent2)">' + (App.isOnline ? '🟢' : '🔴') + '</div><div style="font-size:.75rem;color:var(--text2)">' + (App.isOnline ? '在线' : '离线') + '</div></div>';
    html += '</div>';

    html += '<h4 style="margin-bottom:8px">⚡ 快捷操作</h4>';
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">';
    html += '<button class="btn-sm primary" onclick="Chat.newSession()">💬 新对话</button>';
    html += '<button class="btn-sm" onclick="Tools.openTool(\'知识库管理\')">📚 知识库</button>';
    html += '<button class="btn-sm" onclick="Tools.openTool(\'Agent任务\')">🤖 Agent</button>';
    html += '<button class="btn-sm" onclick="Tools.openTool(\'习惯打卡\')">✅ 打卡</button>';
    html += '</div>';
    html += '</div></div>';

    el.innerHTML = html;
  }
};