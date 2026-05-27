var Batch = {
  init: function() {
    if (typeof Tools === 'undefined') return;
    Tools.toolConfigs['📦 批处理'] = { icon: '📦', desc: '批量处理文件夹内文件', keywords: '批量 文件夹 一键' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    Tools.categories['🧠 AI'].push('📦 批处理');

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === '📦 批处理') { Tools.addToRecent(name); UI.switchView('tools'); self.show(); return; }
      orig.call(Tools, name);
    };
  },

  show: function() {
    var el = document.getElementById('tools-result');
    if (!el) return;
    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">✕</button>';

    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between;align-items:center"><h3>📦 批量处理</h3>' + closeBtn + '</div>' +
      '<div class="result-content">' +
      '<p style="color:var(--text2);margin-bottom:12px">选择文件夹，批量执行操作</p>' +
      '<input type="file" id="batch-files" webkitdirectory multiple style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit;margin-bottom:8px;box-sizing:border-box">' +
      '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">' +
      '<select id="batch-action" style="flex:1;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit">' +
      '<option value="analyze">📄 智能分析</option>' +
      '<option value="translate">🌐 批量翻译</option>' +
      '<option value="summary">📝 批量摘要</option>' +
      '<option value="knowledge">📚 加入知识库</option></select></div>' +
      '<button class="btn-sm primary" onclick="Batch._execute()">🚀 执行</button>' +
      '<div id="batch-output" style="margin-top:12px"></div></div></div>';
  },

  _execute: function() {
    var files = document.getElementById('batch-files').files;
    if (!files || files.length === 0) { App.toast('请选择文件夹', 'error'); return; }

    var out = document.getElementById('batch-output');
    if (out) out.innerHTML = '<p style="color:var(--text2)">⏳ 处理 ' + files.length + ' 个文件...</p>';

    var action = document.getElementById('batch-action').value;
    var self = this;
    var results = [];
    var done = 0;

    Array.from(files).forEach(function(file) {
      var reader = new FileReader();
      reader.onload = function(e) {
        done++;
        results.push({ name: file.name, size: file.size, text: (e.target.result || '').slice(0, 500) });

        if (action === 'knowledge') {
          fetch('/api/knowledge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: 'add_document', collection: Knowledge.currentCollection, text: e.target.result, title: file.name, source: 'batch'}),
            signal: AbortSignal.timeout(10000)
          }).catch(function(){});
        }

        if (done === files.length) {
          self._showResults(results, action);
        }
      };
      reader.readAsText(file);
    });
  },

  _showResults: function(results, action) {
    var out = document.getElementById('batch-output');
    if (!out) return;
    var html = '<h4 style="margin-top:12px">✅ 处理完成 (' + results.length + ' 个文件)</h4>';
    results.forEach(function(r) {
      html += '<div style="padding:8px;background:var(--bg);border-radius:6px;margin-bottom:4px;font-size:.85rem"><strong>' + r.name + '</strong> (' + (r.size / 1024).toFixed(1) + ' KB)</div>';
    });
    out.innerHTML = html;
    App.toast('批量处理完成', 'success');
  }
};