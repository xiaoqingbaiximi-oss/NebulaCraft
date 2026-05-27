var Tools = {
  toolConfigs: {},
  categories: {},
  favorites: [],
  recentTools: [],

  init: function() {
    this.toolConfigs = {
      'Calculator': { icon: '🧮', desc: 'Math/BMI/Loan/Discount', keywords: 'calc BMI loan' },
      'Password Gen': { icon: '🔑', desc: 'Password/UUID/Captcha', keywords: 'password UUID' },
      'Encryption': { icon: '🔒', desc: 'Base64/MD5/SHA', keywords: 'encrypt base64 md5' },
      'Translator': { icon: '🌐', desc: 'Multi-language translate', keywords: 'translate' },
      'QR Code': { icon: '📱', desc: 'Generate QR code', keywords: 'QR code' },
      'Weather': { icon: '🌤️', desc: 'Weather query', keywords: 'weather' },
      'IP Lookup': { icon: '📍', desc: 'IP geolocation', keywords: 'IP' },
      'Jokes': { icon: '😄', desc: 'Random jokes', keywords: 'joke' },
      'Quotes': { icon: '💬', desc: 'Famous quotes', keywords: 'quote' },
      'Poetry': { icon: '📜', desc: 'Classic poetry', keywords: 'poem' },
      'Countdown': { icon: '⏰', desc: 'Date countdown', keywords: 'countdown' },
      'Word Count': { icon: '📏', desc: 'Count words', keywords: 'word count' },
      'Base Convert': { icon: '🔢', desc: 'Number base convert', keywords: 'base hex bin' },
      'Unit Convert': { icon: '⚖️', desc: 'Unit conversion', keywords: 'unit convert' },
      'Color Name': { icon: '🎯', desc: 'Color by hex', keywords: 'color hex' },
      'File Analyze': { icon: '📄', desc: 'Smart file analysis', keywords: 'file analyze' },
      'JSON Format': { icon: '📋', desc: 'JSON formatter', keywords: 'JSON' },
      'Base64': { icon: '🔐', desc: 'Base64 encode/decode', keywords: 'Base64' },
      'Timestamp': { icon: '⏱️', desc: 'Timestamp convert', keywords: 'timestamp' },
      'AI Image': { icon: '🎨', desc: 'AI image generation', keywords: 'AI image SD' },
      'AI Design': { icon: '🖼️', desc: 'Poster/Logo/Illustration', keywords: 'poster logo' },
      'AI Video': { icon: '🎬', desc: 'Text animation/subtitle', keywords: 'video animation' },
      'Code Helper': { icon: '💻', desc: 'Complete/Bug/Review/Refactor', keywords: 'code bug review' },
      'AI Music': { icon: '🎵', desc: 'Algorithmic music composition', keywords: 'music melody chords' },
      'AI 3D Model': { icon: '🎮', desc: 'Text/Image to 3D model', keywords: '3D model mesh' },
      'Mind Map': { icon: '🧠', desc: 'AI generated mind map', keywords: 'mindmap diagram' },
      'Flowchart': { icon: '📊', desc: 'AI generated flowchart', keywords: 'flowchart diagram' },
      'Plugin Market': { icon: '🧩', desc: 'Browse & install plugins', keywords: 'plugin market install' },
    };

    this.categories = {
      'Calc': ['Calculator','Base Convert','Unit Convert','Timestamp'],
      'Security': ['Password Gen','Encryption','Base64'],
      'Writing': ['Translator','Word Count'],
      'Query': ['Weather','IP Lookup','Jokes','Quotes','Poetry','Countdown','Color Name'],
      'Dev': ['JSON Format','QR Code'],
      'File': ['File Analyze'],
      'Creative': ['AI Image', 'AI Design'],
      'Video': ['AI Video'],
      'Code': ['Code Helper'],
      'Audio': ['AI Music'],
      '3D': ['AI 3D Model'],
      'Diagram': ['Mind Map', 'Flowchart'],
      'Plugin': ['Plugin Market'],
    };

    this.loadFavorites();
    this.loadRecent();
    this.render();
    this.bindSearch();
  },

  loadFavorites: function() { try { this.favorites = JSON.parse(localStorage.getItem('nf') || '[]'); } catch(e) { this.favorites = []; } },
  saveFavorites: function() { localStorage.setItem('nf', JSON.stringify(this.favorites)); },
  loadRecent: function() { try { this.recentTools = JSON.parse(localStorage.getItem('nrt') || '[]'); } catch(e) { this.recentTools = []; } },
  saveRecent: function() { localStorage.setItem('nrt', JSON.stringify(this.recentTools.slice(0, 10))); },

  addToRecent: function(name) {
    this.recentTools = this.recentTools.filter(function(t) { return t !== name; });
    this.recentTools.unshift(name);
    this.saveRecent();
  },

  toggleFavorite: function(name) {
    var idx = this.favorites.indexOf(name);
    if (idx > -1) { this.favorites.splice(idx, 1); App.toast('Unfavorited', 'info'); }
    else { this.favorites.push(name); App.toast('Favorited', 'success'); }
    this.saveFavorites();
    this.render();
  },

  closeTool: function() {
    var result = document.getElementById('tools-result');
    if (result) result.innerHTML = '';
    var grid = document.getElementById('tools-grid');
    if (grid) grid.style.display = '';
  },

  render: function(filter) {
    var grid = document.getElementById('tools-grid');
    if (!grid) return;
    grid.style.display = '';
    var self = this;

    var html = '';
    if (!filter) {
      if (this.favorites.length > 0) {
        html += '<div style="grid-column:1/-1;font-size:.85rem;color:var(--text2);margin-top:8px">Favorites</div>';
        this.favorites.forEach(function(name) { var t = self.toolConfigs[name]; if (t) html += self._card(name, t, true); });
      }
      Object.keys(this.categories).forEach(function(cat) {
        html += '<div style="grid-column:1/-1;font-size:.75rem;color:var(--text2);margin-top:12px">' + cat + '</div>';
        (self.categories[cat] || []).forEach(function(name) { var t = self.toolConfigs[name]; if (t) html += self._card(name, t, self.favorites.indexOf(name) !== -1); });
      });
    } else {
      Object.keys(this.toolConfigs).forEach(function(name) {
        if (name.toLowerCase().indexOf(filter.toLowerCase()) !== -1) {
          html += self._card(name, self.toolConfigs[name], self.favorites.indexOf(name) !== -1);
        }
      });
    }

    if (!html && filter) html = '<div class="empty-state" style="grid-column:1/-1">No tools found</div>';
    grid.innerHTML = html;

    grid.querySelectorAll('.tool-card').forEach(function(card) {
      card.addEventListener('click', function() { Tools.openTool(this.dataset.tool); });
    });
    grid.querySelectorAll('.tool-fav').forEach(function(btn) {
      btn.addEventListener('click', function(e) { e.stopPropagation(); Tools.toggleFavorite(this.dataset.tool); });
    });
  },

  _card: function(name, config, isFav) {
    return '<div class="tool-card" data-tool="' + name + '" tabindex="0" style="position:relative">' +
      '<div class="tool-fav" data-tool="' + name + '" style="position:absolute;top:8px;right:8px;cursor:pointer;font-size:1rem;opacity:' + (isFav ? '1' : '0.3') + '">' + (isFav ? '★' : '☆') + '</div>' +
      '<div class="tool-icon">' + config.icon + '</div><div class="tool-name">' + name + '</div><div class="tool-desc">' + config.desc + '</div></div>';
  },

  bindSearch: function() {
    var self = this;
    var input = document.getElementById('tool-search');
    if (!input) return;
    var timer;
    input.addEventListener('input', function() {
      clearTimeout(timer);
      timer = setTimeout(function() { self.render(input.value.trim()); }, 200);
    });
  },

  openTool: function(name) {
    var config = this.toolConfigs[name];
    if (!config) return;
    this.addToRecent(name);
    UI.switchView('tools');
    var result = document.getElementById('tools-result');
    if (!result) return;

    var closeBtn = '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">X</button>';
    var titleBar = '<div style="display:flex;justify-content:space-between;align-items:center"><h3>' + config.icon + ' ' + name + '</h3>' + closeBtn + '</div>';

    if (name === 'JSON Format') { this._showJson(result, titleBar); return; }
    if (name === 'Base64') { this._showBase64(result, titleBar); return; }
    if (name === 'Timestamp') { this._showTimestamp(result, titleBar); return; }
    if (name === 'QR Code') { this._showQR(result, titleBar); return; }
    if (name === 'AI Image') { this._showSD(result, titleBar); return; }
    if (name === 'AI Design') { this._showImageGen(result, titleBar); return; }
    if (name === 'AI Video') { this._showVideoGen(result, titleBar); return; }
    if (name === 'Code Helper') { this._showCode(result, titleBar); return; }
    if (name === 'AI Music') { this._showMusic(result, titleBar); return; }
    if (name === 'AI 3D Model') { this._show3D(result, titleBar); return; }
    if (name === 'Mind Map') { this._showMindMap(result, titleBar); return; }
    if (name === 'Flowchart') { this._showFlowchart(result, titleBar); return; }
    if (name === 'Plugin Market') { this._showPluginMarket(result, titleBar); return; }

    result.innerHTML = '<div class="result-card">' + titleBar +
      '<div class="result-content"><p style="color:var(--text2)">' + config.desc + '</p>' +
      '<textarea id="tool-input" rows="3" placeholder="Input..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit;resize:vertical;min-height:80px;box-sizing:border-box"></textarea></div>' +
      '<div class="result-actions"><button class="btn-sm primary" onclick="Tools._exec(\'' + name + '\')">Execute</button></div>' +
      '<div id="tool-output" class="result-content" style="margin-top:16px;display:none"></div></div>';
  },

  _exec: function(name) {
    var input = document.getElementById('tool-input'), output = document.getElementById('tool-output');
    if (!input || !output) return;
    var text = input.value.trim();
    if (!text) { App.toast('Please enter input', 'error'); return; }
    output.style.display = 'block'; output.innerHTML = 'Processing...';
    var apiMap = { 'Calculator':'/api/calculator','Password Gen':'/api/generator','Encryption':'/api/security','Translator':'/api/translate','Weather':'/api/extra','IP Lookup':'/api/extra','Jokes':'/api/extra','Quotes':'/api/extra','Poetry':'/api/extra','Countdown':'/api/extra','Word Count':'/api/extra','Base Convert':'/api/extra','Unit Convert':'/api/extra','Color Name':'/api/extra' };
    fetch(apiMap[name] || '/api/smart', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text,expression:text,action:'execute'}), signal:AbortSignal.timeout(30000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok) output.textContent = d.reply || d.result || JSON.stringify(d,null,2);
        else output.innerHTML = '<span style="color:var(--danger)">'+(d.error||'Failed')+'</span>';
      }).catch(function(){ output.innerHTML = '<span style="color:var(--danger)">Request failed</span>'; });
  },

  _showPluginMarket: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar + '<div id="pm-list" style="padding:12px"><p>Loading...</p></div></div>';
    this._loadPluginMarket();
  },
  _loadPluginMarket: function() {
    var self = this;
    fetch('/api/marketplace', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'list'})})
      .then(function(r){return r.json();}).then(function(d){
        var list = document.getElementById('pm-list'); if(!list)return;
        if(d.ok && d.plugins){
          var html = '<div style="display:flex;flex-direction:column;gap:8px">';
          d.plugins.forEach(function(p){
            html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px;background:var(--bg);border-radius:8px;border:1px solid var(--border)">' +
              '<div style="display:flex;align-items:center;gap:12px"><span style="font-size:24px">'+(p.icon||'📦')+'</span>' +
              '<div><div style="font-weight:600">'+p.name+'</div><div style="font-size:.8rem;color:var(--text2)">'+p.description+'</div></div></div>' +
              (p.installed ? '<button onclick="Tools._uninstallPlugin(\''+p.id+'\')" style="background:var(--danger);color:white;border:none;padding:6px 12px;border-radius:6px;cursor:pointer">卸载</button>' :
              '<button onclick="Tools._installPlugin(\''+p.id+'\')" style="background:var(--accent-color);color:white;border:none;padding:6px 12px;border-radius:6px;cursor:pointer">安装</button>') + '</div>';
          });
          html += '</div>'; list.innerHTML = html;
        }
      });
  },
  _installPlugin: function(id) {
    var self = this;
    fetch('/api/marketplace', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'install',plugin_id:id})})
      .then(function(r){return r.json();}).then(function(d){ App.toast(d.ok?'Installed!':(d.error||'Failed'), d.ok?'success':'error'); self._loadPluginMarket(); });
  },
  _uninstallPlugin: function(id) {
    var self = this;
    fetch('/api/marketplace', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'uninstall',plugin_id:id})})
      .then(function(r){return r.json();}).then(function(d){ App.toast(d.ok?'Uninstalled!':(d.error||'Failed'), d.ok?'success':'error'); self._loadPluginMarket(); });
  },

  _showMusic: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<input id="music-prompt" placeholder="Style" style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<select id="music-tempo" style="width:100%;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px"><option value="120">120 BPM</option><option value="80">80 BPM</option><option value="160">160 BPM</option></select>' +
      '<button class="btn-sm primary" onclick="Tools._musicGenerate()" style="margin-top:8px">Generate</button>' +
      '<div id="music-output" style="margin-top:12px;text-align:center"></div></div>';
  },
  _musicGenerate: function() {
    var prompt = document.getElementById('music-prompt').value.trim();
    var tempo = parseInt(document.getElementById('music-tempo').value) || 120;
    var out = document.getElementById('music-output');
    if (out) out.innerHTML = '<p>🎵 Generating...</p>';
    fetch('/api/music', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'text', prompt:prompt||'欢快', tempo:tempo}), signal:AbortSignal.timeout(60000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;
        if(d.ok){out.innerHTML='<div style="padding:16px"><div style="font-size:48px">🎵</div><p>'+d.style+' | '+d.tempo+' BPM</p><audio controls style="max-width:300px"><source src="'+d.url+'" type="audio/midi"></audio><p><a href="'+d.url+'" download>Download</a></p></div>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>';}
      });
  },

  _show3D: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<input id="d3-prompt" placeholder="Describe object..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<button class="btn-sm primary" onclick="Tools._3dGenerate()">Generate</button>' +
      '<div id="d3-output" style="margin-top:12px;text-align:center"></div></div>';
  },
  _3dGenerate: function() {
    var prompt = document.getElementById('d3-prompt').value.trim();
    if (!prompt) { App.toast('Please enter description', 'error'); return; }
    var out = document.getElementById('d3-output');
    if (out) out.innerHTML = '<p>🎮 Generating 3D model...</p>';
    fetch('/api/3d/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({prompt:prompt}), signal:AbortSignal.timeout(180000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;
        if(d.ok && window.TDViewer){out.innerHTML=''; TDViewer.createPreview(d.model_base64, out);}
        else if(d.ok){out.innerHTML='<p>3D model ready! <a href="#" onclick="TDViewer.downloadModel(\''+d.model_base64+'\')">Download</a></p>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>';}
      });
  },

  _showMindMap: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<input id="mm-topic" placeholder="Topic..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<button class="btn-sm primary" onclick="Tools._mindmapGenerate()">Generate</button>' +
      '<div id="mm-output" style="margin-top:12px"></div></div>';
  },
  _mindmapGenerate: function() {
    var topic = document.getElementById('mm-topic').value.trim();
    if (!topic) { App.toast('Please enter topic', 'error'); return; }
    var out = document.getElementById('mm-output');
    if (out) out.innerHTML = '<p>🧠 Generating...</p>';
    var prompt = '请为以下主题生成一个思维导图，用 Mermaid mindmap 语法输出。分3-6个分支，每分支2-4个子节点，直接输出代码，不要任何解释，用中文。\n\n主题：' + topic;
    fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:prompt, model:'deepseek-chat'}), signal: AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){
          var code = d.reply.replace(/```mermaid\n?/g,'').replace(/```/g,'').trim();
          if(!code.startsWith('mindmap')) code = 'mindmap\n  ' + topic + '\n' + code;
          if(out){
            var uniqueId = 'mm-' + Date.now();
            out.innerHTML = '<div class="mermaid" id="' + uniqueId + '" style="background:#fff;border-radius:8px;padding:16px;text-align:center;">' + code + '</div>';
            setTimeout(function(){
              var el = document.getElementById(uniqueId);
              if(el && typeof mermaid !== 'undefined'){ el.removeAttribute('data-processed'); mermaid.run({nodes:[el]}); }
            }, 300);
          }
        } else { out.innerHTML = '<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>'; }
      }).catch(function(){ out.innerHTML = '<div style="color:var(--danger)">Request failed</div>'; });
  },

  _showFlowchart: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<input id="fc-topic" placeholder="Flow..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<button class="btn-sm primary" onclick="Tools._flowchartGenerate()">Generate</button>' +
      '<div id="fc-output" style="margin-top:12px"></div></div>';
  },
  _flowchartGenerate: function() {
    var topic = document.getElementById('fc-topic').value.trim();
    if (!topic) { App.toast('Please enter flow', 'error'); return; }
    var out = document.getElementById('fc-output');
    if (out) out.innerHTML = '<p>📊 Generating...</p>';
    var prompt = '请为以下流程生成一个流程图，用 Mermaid flowchart LR 语法输出。直接输出代码，不要任何解释，用中文。\n\n流程：' + topic;
    fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:prompt, model:'deepseek-chat'}), signal: AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){
          var code = d.reply.replace(/```mermaid\n?/g,'').replace(/```/g,'').trim();
          if(!code.startsWith('flowchart')) code = 'flowchart LR\n  ' + code;
          if(out){
            var uniqueId = 'fc-' + Date.now();
            out.innerHTML = '<div class="mermaid" id="' + uniqueId + '" style="background:#fff;border-radius:8px;padding:16px;text-align:center;">' + code + '</div>';
            setTimeout(function(){
              var el = document.getElementById(uniqueId);
              if(el && typeof mermaid !== 'undefined'){ el.removeAttribute('data-processed'); mermaid.run({nodes:[el]}); }
            }, 300);
          }
        } else { out.innerHTML = '<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>'; }
      }).catch(function(){ out.innerHTML = '<div style="color:var(--danger)">Request failed</div>'; });
  },

  _showSD: function(result, titleBar) {
    var html = '<div class="result-card">' + titleBar +
      '<input id="sd-prompt" placeholder="Describe the image..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<select id="sd-platform" style="width:100%;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px">' +
      '<option value="">自动选择</option><option value="pollinations">Pollinations.ai</option><option value="pillow">内置引擎</option></select>' +
      '<select id="sd-style" style="width:100%;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px"><option value="">Auto</option><option value="写实">写实</option><option value="动漫">动漫</option><option value="油画">油画</option><option value="水彩">水彩</option><option value="赛博朋克">赛博朋克</option><option value="像素">像素</option><option value="素描">素描</option><option value="3D渲染">3D渲染</option></select>' +
      '<button class="btn-sm primary" onclick="Tools._sdGenerate()">Generate</button>' +
      '<div id="sd-output" style="margin-top:12px;text-align:center"></div></div>';
    result.innerHTML = html;
    fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'status'})})
      .then(function(r){return r.json();}).then(function(d){
        var sel = document.getElementById('sd-platform');
        if(!sel) return;
        sel.innerHTML = '<option value="">自动选择</option>';
        var platforms = d.platforms || {};
        if (platforms.qwen && platforms.qwen.has_key) sel.innerHTML += '<option value="qwen">通义万相</option>';
        if (platforms.openai && platforms.openai.has_key) sel.innerHTML += '<option value="openai">OpenAI DALL-E</option>';
        if (platforms.google && platforms.google.has_key) sel.innerHTML += '<option value="gemini">Google Gemini</option>';
        sel.innerHTML += '<option value="sd_webui">SD WebUI/ComfyUI</option>';
        sel.innerHTML += '<option value="pollinations">Pollinations.ai</option>';
        sel.innerHTML += '<option value="pillow">内置引擎</option>';
      });
  },
  _sdGenerate: function() {
    var prompt=document.getElementById('sd-prompt').value.trim();if(!prompt){App.toast('Please enter description','error');return;}
    var out=document.getElementById('sd-output');if(out)out.innerHTML='<p>Generating...</p>';
    var platform=document.getElementById('sd-platform').value;
    var style=document.getElementById('sd-style').value;
    var body = {prompt:prompt, style:style||'auto', width:1024, height:1024};
    if (platform) body.platform = platform;
    fetch('/api/image_gen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(120000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;if(d.ok){out.innerHTML='<img src="'+d.url+'" style="max-width:100%;border-radius:12px"><p>'+d.category+'</p>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>';}
      });
  },

  _showImageGen: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<input id="ig-prompt" placeholder="Describe..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box">' +
      '<select id="ig-style" style="width:100%;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px"><option value="auto">Auto</option><option value="poster">Poster</option><option value="illustration">Illustration</option><option value="logo">Logo</option><option value="photo">Photo</option></select>' +
      '<button class="btn-sm primary" onclick="Tools._igGenerate()">Generate</button><div id="ig-output" style="margin-top:12px;text-align:center"></div></div>';
  },
  _igGenerate: function() {
    var prompt=document.getElementById('ig-prompt').value.trim();if(!prompt){App.toast('Please enter description','error');return;}
    var out=document.getElementById('ig-output');if(out)out.innerHTML='<p>Generating...</p>';
    var style=document.getElementById('ig-style').value;
    fetch('/api/image_gen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:prompt,style:style,width:1024,height:1024}),signal:AbortSignal.timeout(60000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;if(d.ok){out.innerHTML='<img src="'+d.url+'" style="max-width:100%;border-radius:12px"><p>'+d.category+'</p>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>';}
      });
  },

  _showVideoGen: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<textarea id="vg-text" rows="4" placeholder="Input text..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px;box-sizing:border-box"></textarea>' +
      '<select id="vg-action" style="width:100%;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);margin-bottom:8px"><option value="text">Text Animation</option><option value="subtitles">Subtitles</option></select>' +
      '<button class="btn-sm primary" onclick="Tools._vgGenerate()">Generate</button><div id="vg-output" style="margin-top:12px"></div></div>';
  },
  _vgGenerate: function() {
    var text=document.getElementById('vg-text').value.trim();if(!text){App.toast('Please input text','error');return;}
    var out=document.getElementById('vg-output');if(out)out.innerHTML='<p>Generating...</p>';
    var action=document.getElementById('vg-action').value;
    fetch('/api/video_gen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:action,text:text,duration:5}),signal:AbortSignal.timeout(120000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;
        if(d.ok){out.innerHTML='<video src="'+d.url+'" controls style="max-width:100%;border-radius:12px"></video><p><a href="'+d.url+'" download>Download</a></p>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Need ffmpeg')+'</div>';}
      });
  },

  _showCode: function(result, titleBar) {
    result.innerHTML = '<div class="result-card">' + titleBar +
      '<textarea id="ch-code" rows="8" placeholder="Paste code..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;min-height:150px;box-sizing:border-box;margin-bottom:8px;font-size:.85rem"></textarea>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn-sm primary" onclick="Tools._chAction(\'complete\')">Complete</button><button class="btn-sm" onclick="Tools._chAction(\'bugs\')">Find Bugs</button><button class="btn-sm" onclick="Tools._chAction(\'review\')">Review</button><button class="btn-sm" onclick="Tools._chAction(\'explain\')">Explain</button></div>' +
      '<div id="ch-output" style="margin-top:12px"></div></div>';
  },
  _chAction: function(action) {
    var code=document.getElementById('ch-code').value.trim();
    var out=document.getElementById('ch-output');if(!out)return;
    if(!code){App.toast('Please paste code','error');return;}
    out.innerHTML='<p>Analyzing...</p>';
    fetch('/api/code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:action,code:code,language:'python'}),signal:AbortSignal.timeout(120000)})
      .then(function(r){return r.json();}).then(function(d){
        if(!out)return;
        if(d.ok){var key=action==='complete'?'completion':action==='bugs'?'analysis':action==='review'?'review':'explanation';
          out.innerHTML='<pre style="background:var(--bg);padding:16px;border-radius:8px;font-family:monospace;font-size:.85rem;max-height:500px;overflow-y:auto;white-space:pre-wrap">'+Tools._escHtml(d[key]||'No result')+'</pre>';}
        else{out.innerHTML='<div style="color:var(--danger)">'+(d.error||'Failed')+'</div>';}
      });
  },
  _escHtml: function(s) { var d=document.createElement('div'); d.textContent=(s||''); return d.innerHTML; }
};