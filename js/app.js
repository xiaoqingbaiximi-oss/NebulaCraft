var App = {
  version: '7.0.0',
  isOnline: false,
  currentModel: 'qwen2.5:1.5b',
  settings: {},

  init: function() {
    console.log('NebulaCraft v' + this.version + ' ready');
    this.loadSettings();
    this.currentModel = this.settings.model || 'qwen2.5:1.5b';
    this.loadModels();
    this.checkOnline();
    Chat.init();
    if (typeof Tools !== 'undefined') Tools.init();
    if (typeof Knowledge !== 'undefined') Knowledge.init();
    if (typeof UI !== 'undefined') UI.init();
  },

  loadSettings: function() {
    try {
      this.settings = JSON.parse(localStorage.getItem('nebula_settings') || '{}');
    } catch(e) {
      this.settings = {};
    }
  },

  saveSettings: function() {
    this.settings.model = this.currentModel;
    localStorage.setItem('nebula_settings', JSON.stringify(this.settings));
  },

  loadModels: function() {
    var self = this;
    fetch('/api/models/list', { signal: AbortSignal.timeout(5000) })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        var sel = document.getElementById('model-select');
        if (sel && d.models) {
          sel.innerHTML = d.models.map(function(m) {
            var name = m.name;
            var label = name.length > 20 ? name.substring(0, 17) + '...' : name;
            return '<option value="' + name + '"' + (name === self.currentModel ? ' selected' : '') + '>' + label + '</option>';
          }).join('');
        }
      })
      .catch(function() {});
  },

  setModel: function(model) {
    this.currentModel = model;
    this.saveSettings();
    this.toast('Model: ' + model);
  },

  checkOnline: function() {
    var self = this;
    this.isOnline = true;
    fetch('/health', { signal: AbortSignal.timeout(3000) })
      .then(function() { self.isOnline = true; })
      .catch(function() { self.isOnline = false; });
  },

  toast: function(msg, type) {
    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px';
      document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.style.cssText = 'padding:10px 18px;border-radius:8px;color:#fff;font-size:.85rem;animation:fadeIn 0.3s;max-width:350px;word-break:break-word';
    if (type === 'error') toast.style.background = '#ef4444';
    else if (type === 'success') toast.style.background = '#16a34a';
    else toast.style.background = 'var(--accent-color, #6c5ce7)';
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(function() {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(function() { toast.remove(); }, 300);
    }, 2500);
  },

  showSettings: function() {
    var self = this;
    fetch('/api/settings', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'status'}) })
      .then(function(r){return r.json();})
      .then(function(d){
        var overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center';
        var platformsHtml = '';
        var platforms = d.platforms || {};
        for (var key in platforms) {
          var p = platforms[key];
          var active = d.active === key ? ' ✅' : '';
          var helpUrl = '';
          if (key === 'qwen') helpUrl = 'https://dashscope.console.aliyun.com';
          else if (key === 'deepseek') helpUrl = 'https://platform.deepseek.com';
          else if (key === 'openai') helpUrl = 'https://platform.openai.com';
          else if (key === 'google') helpUrl = 'https://aistudio.google.com/apikey';

          platformsHtml += '<div style="margin-bottom:12px;padding:12px;background:var(--bg-secondary,#16213e);border-radius:8px;border:1px solid var(--border)">' +
            '<div style="font-weight:600;margin-bottom:6px">' + p.name + active + '</div>' +
            '<div style="display:flex;gap:8px">' +
            '<input type="password" id="key-' + key + '" placeholder="' + p.name + ' API Key" value="' + (p.has_key ? '••••••••' : '') + '" style="flex:1;padding:8px;border-radius:6px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-size:.8rem">' +
            '<button onclick="App.savePlatformKey(\'' + key + '\')" style="background:var(--accent-color,#6c5ce7);color:white;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:.8rem;white-space:nowrap">保存</button>' +
            '</div>' +
            (helpUrl ? '<div style="font-size:.7rem;color:var(--text2);margin-top:4px"><a href="' + helpUrl + '" target="_blank" style="color:var(--accent-color)">获取 Key →</a></div>' : '') +
            '</div>';
        }
        overlay.innerHTML = '<div style="background:var(--bg,#1a1a2e);padding:24px;border-radius:12px;min-width:450px;max-width:550px;max-height:80vh;overflow-y:auto">' +
          '<h3 style="margin-bottom:16px">⚙️ 多平台 API 设置</h3>' +
          '<p style="font-size:.8rem;color:var(--text2);margin-bottom:12px">设置任一平台即可使用，保存后自动切换</p>' +
          platformsHtml +
          '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">' +
          '<button onclick="this.closest(\'div\').parentElement.remove()" style="background:var(--border);color:var(--text);border:none;padding:8px 16px;border-radius:6px;cursor:pointer">关闭</button>' +
          '</div></div>';
        document.body.appendChild(overlay);
        overlay.addEventListener('click', function(e){ if(e.target === overlay) overlay.remove(); });
      });
  },

  savePlatformKey: function(platform) {
    var key = document.getElementById('key-' + platform).value.trim();
    if (!key || key === '••••••••') { this.toast('请输入 ' + platform + ' API Key', 'error'); return; }
    var self = this;
    fetch('/api/settings', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'set_api_key', platform:platform, api_key:key}) })
      .then(function(r){return r.json();})
      .then(function(d){
        if (d.ok) {
          self.toast(platform + ' API Key 已保存！', 'success');
          var overlay = document.querySelector('div[style*="position:fixed"]');
          if (overlay) overlay.remove();
        } else {
          self.toast(d.error || 'Failed', 'error');
        }
      });
  },

  toggleTheme: function() {
    var html = document.documentElement;
    var current = html.getAttribute('data-theme') || 'dark';
    var next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    this.toast('主题: ' + (next === 'dark' ? '深色' : '浅色'), 'info');
  },

  toggleAutoTheme: function(val) {
    if (val) {
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
      this.toast('已开启跟随系统', 'success');
    }
  },

  toggleSetting: function(name) {
    var html = document.documentElement;
    if (name === 'highContrast') {
      html.classList.toggle('high-contrast');
      this.toast('高对比度: ' + (html.classList.contains('high-contrast') ? '开' : '关'), 'info');
    } else if (name === 'dyslexiaFont') {
      html.classList.toggle('dyslexia-font');
      this.toast('阅读障碍字体: ' + (html.classList.contains('dyslexia-font') ? '开' : '关'), 'info');
    }
  },

  setFontSize: function(val) {
    document.documentElement.style.fontSize = val + 'px';
    var el = document.getElementById('font-size-val');
    if (el) el.textContent = val;
  },

  showCheatsheet: function() {
    this.toast('指令: @思维导图 @流程图 @音乐 @生成3D @代码 @agent @分析 @定时 @生成', 'info');
  },

  toggleLang: function() {
    this.toast('语言切换', 'info');
  }

};