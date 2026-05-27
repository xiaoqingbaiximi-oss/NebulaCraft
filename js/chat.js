var Chat = {
  sessionId: 'default',
  isStreaming: false,
  abortController: null,
  lastUploadedImage: null,

  init: function() {
    this.input = document.getElementById('chat-input');
    this.messagesContainer = document.getElementById('messages');
    this.bindEvents();
    this.updateWordCount();
  },

  bindEvents: function() {
    var self = this;
    var sendBtn = document.querySelector('.btn-send');
    if (sendBtn) sendBtn.addEventListener('click', function() { self.send(); });

    if (this.input) {
      this.input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); self.send(); }
      });
      this.input.addEventListener('input', function() {
        self.autoResize();
        self.updateWordCount();
      });
    }

    document.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'k') { e.preventDefault(); var s = document.getElementById('tool-search'); if (s) s.focus(); }
      if (e.ctrlKey && e.key === 'n') { e.preventDefault(); self.newSession(); }
    });
  },

  send: function() {
    var text = this.input.value.trim();
    if (!text || this.isStreaming) return;

    if (text.startsWith('@screenshot') || text.startsWith('@截图')) {
      this.captureScreen();
      return;
    }

    if (text.startsWith('@analyze') || text.startsWith('@屏幕') || text.startsWith('@分析')) {
      var question = text.replace(/@analyze|@屏幕|@分析/, '').trim();
      if (!this.lastUploadedImage) { this.addMessage('ai', 'Please capture a screenshot first.', true); return; }
      this.analyzeScreen(this.lastUploadedImage, question || '请描述截图');
      return;
    }

    // ===== @生成 图片 =====
    if (text.startsWith('@生成') && !text.startsWith('@生成3D')) {
      var prompt = text.replace(/@生成/, '').trim();
      if (!prompt) { this.addMessage('ai', '请描述图片内容', true); return; }
      var self = this;
      this.input.value = '';
      this.autoResize();
      var encoded = encodeURIComponent(prompt);
      var url = 'https://image.pollinations.ai/prompt/' + encoded + '?width=1024&height=1024&nologo=true';
      var mc = self.addMessage('ai', '', false);
      var b = mc.querySelector('.msg-bubble');
      if (b) {
        b.innerHTML = '<p>🎨 正在生成...</p><img src="' + url + '" style="max-width:100%;border-radius:12px;display:none" onload="this.style.display=\'block\';this.previousElementSibling.style.display=\'none\'" onerror="this.previousElementSibling.textContent=\'❌ 生成失败，请重试\'">';
      }
      return;
    }

    if (text.startsWith('@思维导图') || text.startsWith('@脑图') || text.startsWith('@mindmap')) {
      var topic = text.replace(/@思维导图|@脑图|@mindmap/, '').trim();
      if (!topic) { this.addMessage('ai', '请提供主题', true); return; }
      this.generateMindmap(topic);
      return;
    }

    if (text.startsWith('@流程图') || text.startsWith('@flowchart')) {
      var flowTopic = text.replace(/@流程图|@flowchart/, '').trim();
      if (!flowTopic) { this.addMessage('ai', '请描述流程', true); return; }
      this.generateFlowchart(flowTopic);
      return;
    }

    if (text.startsWith('@代码') || text.startsWith('@code')) {
      var codeTask = text.replace(/@代码|@code/, '').trim();
      if (!codeTask) { this.addMessage('ai', '请描述需求', true); return; }
      this.generateCode(codeTask);
      return;
    }

    if (text.startsWith('@agent') || text.startsWith('@auto') || text.startsWith('@自动')) {
      var task = text.replace(/@agent|@auto|@自动/, '').trim();
      if (!task) { this.addMessage('ai', '请描述任务', true); return; }
      var self = this;
      this.input.value = ''; this.autoResize();
      var loadingMsg = this.addMessage('ai', '🤖 Agent 正在执行...', false, true);
      fetch('/api/agent', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:task}) })
        .then(function(r){return r.json();}).then(function(d){
          loadingMsg.remove();
          if(d.ok){ self.addMessage('ai', '## Agent 报告\n\n**任务**: '+d.user_input+'\n**步骤数**: '+d.steps_count+'\n\n### 总结\n'+d.summary); }
          else{ self.addMessage('ai', '❌ '+(d.error||'Failed'), true); }
        }).catch(function(){ loadingMsg.remove(); });
      return;
    }

    if (text.startsWith('@音乐') || text.startsWith('@music')) {
      var musicPrompt = text.replace(/@音乐|@music/, '').trim();
      var self = this;
      this.input.value = ''; this.autoResize();
      var loadingMsg = this.addMessage('ai', '🎵 正在生成音乐...', false, true);
      var requestBody = { action: 'full' };
      if (musicPrompt) { requestBody.prompt = musicPrompt; requestBody.action = 'text'; }
      fetch('/api/music', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody) })
        .then(function(r){return r.json();}).then(function(d){
          loadingMsg.remove();
          if(d.ok){
            var mc = self.addMessage('ai', '', false);
            var b = mc.querySelector('.msg-bubble');
            if(b){ b.innerHTML = '<div style="text-align:center"><div style="font-size:48px">🎵</div><p>'+d.style+' | '+d.tempo+' BPM</p><audio controls style="max-width:300px"><source src="'+d.url+'" type="audio/midi"></audio><p><a href="'+d.url+'" download>Download</a></p></div>'; }
          } else { self.addMessage('ai', '❌ '+(d.error||'Failed'), true); }
        }).catch(function(){ loadingMsg.remove(); });
      return;
    }

    if (text.startsWith('@生成3D') || text.startsWith('@3d')) {
      var prompt = text.replace(/@生成3D|@3d/, '').trim();
      var self = this;
      if (!prompt && !this.lastUploadedImage) { this.addMessage('ai', '请提供描述或上传图片', true); return; }
      this.input.value = ''; this.autoResize();
      var loadingMsg = this.addMessage('ai', '🎮 Generating 3D model...', false, true);
      var requestBody = {};
      if (this.lastUploadedImage) { requestBody.image_base64 = this.lastUploadedImage; this.lastUploadedImage = null; }
      else { requestBody.prompt = prompt; }
      fetch('/api/3d/generate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(requestBody) })
        .then(function(r){return r.json();}).then(function(d){
          loadingMsg.remove();
          if(d.ok){
            var mc = self.addMessage('ai', '', false);
            var b = mc.querySelector('.msg-bubble');
            if(b && window.TDViewer){ b.innerHTML=''; TDViewer.createPreview(d.model_base64, b); }
            else if(b){ b.innerHTML='<p><a href="#" onclick="TDViewer.downloadModel(\''+d.model_base64+'\')">Download</a></p>'; }
          } else { self.addMessage('ai', '❌ '+(d.error||'Failed'), true); }
        }).catch(function(){ loadingMsg.remove(); });
      return;
    }

    // 普通对话
    this.input.value = ''; this.autoResize();
    this.addMessage('user', text);

    var self = this;
    var loadingMsg = this.addMessage('ai', 'Thinking...', false, true);
    this.isStreaming = true;
    this.abortController = new AbortController();

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, model: App.currentModel, session_id: this.sessionId }),
      signal: AbortSignal.timeout(120000)
    }).then(function(r){return r.json();}).then(function(d){
      loadingMsg.remove();
      self.isStreaming = false;
      if(d.ok){ self.addMessage('ai', d.reply); self.saveToHistory('ai', d.reply); }
      else{ self.addMessage('ai', '❌ '+(d.error||'Unknown'), true); }
    }).catch(function(){
      loadingMsg.remove();
      self.isStreaming = false;
      self.addMessage('ai', 'Request failed', true);
    });
  },

  generateCode: function(task) {
    var self = this;
    var loadingMsg = this.addMessage('ai', '💻 Generating code...', false, true);
    fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:'Generate complete runnable code for: '+task, model:'deepseek-chat'}), signal:AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){
          var code = d.reply.replace(/```[a-z]*\n?/g,'').replace(/```/g,'').trim();
          loadingMsg.classList.remove('loading');
          var bubble = loadingMsg.querySelector('.msg-bubble');
          var cid = 'code-'+Date.now();
          if(bubble){ bubble.innerHTML = '<div style="font-weight:600">💻 Code</div><pre id="'+cid+'" style="background:#0d1117;padding:16px;border-radius:8px;max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap">'+self.escapeHtml(code)+'</pre><div style="margin-top:8px;display:flex;gap:8px"><button onclick="Chat.copyCode(\''+cid+'\')" style="background:var(--accent-color);color:white;border:none;padding:6px 14px;border-radius:6px;cursor:pointer">📋 Copy</button><button onclick="Chat.downloadCode(\''+cid+'\')" style="background:var(--accent-color);color:white;border:none;padding:6px 14px;border-radius:6px;cursor:pointer">⬇ Download</button></div>'; }
        } else { loadingMsg.querySelector('.msg-bubble').textContent = '❌ Failed'; }
      }).catch(function(){ loadingMsg.querySelector('.msg-bubble').textContent = '❌ Request failed'; });
  },
  copyCode: function(id){ var el=document.getElementById(id); if(el){ navigator.clipboard.writeText(el.textContent); App.toast('Copied!','success'); } },
  downloadCode: function(id){ var el=document.getElementById(id); if(el){ this.downloadFile('code.html',el.textContent,'text/html'); } },

  generateMindmap: function(topic) {
    var self = this;
    var loadingMsg = this.addMessage('ai', '🧠 Generating mind map...', false, true);
    var prompt = '请为以下主题生成一个思维导图，用 Mermaid mindmap 语法输出。分3-6个分支，每分支2-4个子节点，直接输出代码，不要任何解释，用中文。\n\n主题：' + topic;
    fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:prompt, model:'deepseek-chat'}), signal: AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){
          var code = d.reply.replace(/```mermaid\n?/g,'').replace(/```/g,'').trim();
          if(!code.startsWith('mindmap')) code = 'mindmap\n  ' + topic + '\n' + code;
          var bubble = loadingMsg.querySelector('.msg-bubble');
          if (bubble) {
            loadingMsg.classList.remove('loading');
            var uniqueId = 'mermaid-' + Date.now();
            bubble.innerHTML = '<div style="margin-bottom:8px;font-weight:600;">🧠 思维导图: ' + self.escapeHtml(topic) + '</div>' +
              '<div class="mermaid" id="' + uniqueId + '" style="background:#fff;border-radius:8px;padding:16px;text-align:center;">' + code + '</div>';
            setTimeout(function() {
              var el = document.getElementById(uniqueId);
              if (el && typeof mermaid !== 'undefined') {
                el.removeAttribute('data-processed');
                mermaid.run({ nodes: [el] });
              }
            }, 300);
          }
        } else {
          loadingMsg.classList.add('error');
          loadingMsg.querySelector('.msg-bubble').textContent = '❌ ' + (d.error || 'Failed');
        }
      }).catch(function(){
        loadingMsg.classList.add('error');
        loadingMsg.querySelector('.msg-bubble').textContent = '❌ Request failed';
      });
  },

  generateFlowchart: function(topic) {
    var self = this;
    var loadingMsg = this.addMessage('ai', '📊 Generating flowchart...', false, true);
    var prompt = '请为以下流程生成一个流程图，用 Mermaid flowchart LR 语法输出。直接输出代码，不要任何解释，用中文。\n\n流程：' + topic;
    fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:prompt, model:'deepseek-chat'}), signal: AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){
          var code = d.reply.replace(/```mermaid\n?/g,'').replace(/```/g,'').trim();
          if(!code.startsWith('flowchart')) code = 'flowchart LR\n  ' + code;
          var bubble = loadingMsg.querySelector('.msg-bubble');
          if (bubble) {
            loadingMsg.classList.remove('loading');
            var uniqueId = 'mermaid-' + Date.now();
            bubble.innerHTML = '<div style="margin-bottom:8px;font-weight:600;">📊 流程图: ' + self.escapeHtml(topic) + '</div>' +
              '<div class="mermaid" id="' + uniqueId + '" style="background:#fff;border-radius:8px;padding:16px;text-align:center;">' + code + '</div>';
            setTimeout(function() {
              var el = document.getElementById(uniqueId);
              if (el && typeof mermaid !== 'undefined') {
                el.removeAttribute('data-processed');
                mermaid.run({ nodes: [el] });
              }
            }, 300);
          }
        } else {
          loadingMsg.classList.add('error');
          loadingMsg.querySelector('.msg-bubble').textContent = '❌ ' + (d.error || 'Failed');
        }
      }).catch(function(){
        loadingMsg.classList.add('error');
        loadingMsg.querySelector('.msg-bubble').textContent = '❌ Request failed';
      });
  },

  captureScreen: function() {
    var self = this;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) { App.toast('Not supported', 'error'); return; }
    navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: 'screen' }, audio: false })
      .then(function(stream) {
        var video = document.createElement('video'); video.srcObject = stream;
        video.onloadedmetadata = function() {
          video.play();
          var canvas = document.createElement('canvas'); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
          var ctx = canvas.getContext('2d'); ctx.drawImage(video, 0, 0);
          stream.getTracks().forEach(function(t) { t.stop(); });
          var base64 = canvas.toDataURL('image/png');
          self.lastUploadedImage = base64.split(',')[1];
          var mc = self.addMessage('user', '', false);
          var b = mc.querySelector('.msg-bubble');
          if (b) b.innerHTML = '<img src="' + base64 + '" style="max-width:300px;border-radius:8px;"><br><small>📸 Type @analyze</small>';
        };
      }).catch(function() {});
  },
  analyzeScreen: function(b64, q) {
    var self = this;
    var lm = this.addMessage('ai', '🔍 Analyzing...', false, true);
    fetch('/api/multimodal', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({image_base64:b64, prompt:q||'描述这张截图', model:App.currentModel}), signal:AbortSignal.timeout(120000) })
      .then(function(r){return r.json();}).then(function(d){ lm.remove(); self.addMessage('ai', d.ok?d.reply:'❌ Failed'); })
      .catch(function(){ lm.remove(); });
  },

  addMessage: function(role, content, isError, isLoading) {
    var msg = document.createElement('div');
    msg.className = 'msg ' + role;
    if (isError) msg.classList.add('error');
    if (isLoading) msg.classList.add('loading');
    var avatar = role === 'user' ? 'U' : 'AI';
    var time = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    var bubbleContent = isLoading ? content : this.renderMarkdown(content);
    msg.innerHTML = '<div class="msg-avatar">' + avatar + '</div>' +
      '<div class="msg-body"><div class="msg-bubble">' + bubbleContent + '</div>' +
      '<div class="msg-meta"><span class="msg-time">' + time + '</span>' +
      '<span class="msg-actions">' + (role === 'ai' ? '<button onclick="Chat.copyMessage(this)">Copy</button><button onclick="Chat.speakMessage(this)">Speak</button>' : '<button onclick="Chat.deleteMessage(this)">Del</button>') + '</span></div></div>';
    this.messagesContainer.appendChild(msg);
    this.scrollToBottom();
    return msg;
  },

  renderMarkdown: function(text) {
    if (!text) return '';
    if (typeof marked === 'undefined') return this.escapeHtml(text).replace(/\n/g, '<br>');
    try { var html = marked.parse(text); if (typeof DOMPurify !== 'undefined') html = DOMPurify.sanitize(html); return html; }
    catch(e) { return this.escapeHtml(text).replace(/\n/g, '<br>'); }
  },

  escapeHtml: function(text) { var d = document.createElement('div'); d.textContent = text; return d.innerHTML; },
  copyMessage: function(btn) { var b = btn.closest('.msg-body').querySelector('.msg-bubble'); if (b) { navigator.clipboard.writeText(b.textContent); App.toast('Copied', 'success'); } },
  speakMessage: function(btn) { var b = btn.closest('.msg-body').querySelector('.msg-bubble'); if (b && 'speechSynthesis' in window) { window.speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance(b.textContent); u.lang = 'zh-CN'; u.rate = 1.0; window.speechSynthesis.speak(u); } },
  deleteMessage: function(btn) { var m = btn.closest('.msg'); if (m) { m.style.opacity = '0'; m.style.transition = 'all 0.3s'; setTimeout(function() { m.remove(); }, 300); } },
  newSession: function() { this.sessionId = 'session_' + Date.now(); if (this.messagesContainer) { this.messagesContainer.innerHTML = '<div class="welcome"><div class="welcome-icon">+</div><h2>New Session</h2></div>'; } App.toast('New session', 'info'); },
  uploadFile: function() { var i = document.getElementById('file-input'); if (i) i.click(); },
  startVoice: function() { if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) { App.toast('Speech not supported', 'error'); return; } var SR = window.SpeechRecognition || window.webkitSpeechRecognition; var rec = new SR(); rec.lang = 'zh-CN'; rec.onresult = function(e) { Chat.input.value = e.results[0][0].transcript; Chat.autoResize(); }; rec.onerror = function() { App.toast('Speech failed', 'error'); }; rec.start(); App.toast('Listening...', 'info'); },
  exportHistory: function() { var ms = this.messagesContainer.querySelectorAll('.msg'); var t = '# Chat\n\n'; ms.forEach(function(m) { var r = m.classList.contains('user') ? 'User' : 'AI'; t += '## ' + r + '\n' + (m.querySelector('.msg-bubble').textContent || '') + '\n\n---\n\n'; }); this.downloadFile('chat-' + Date.now() + '.md', t, 'text/markdown'); },
  downloadFile: function(name, content, type) { var blob = new Blob([content], { type: type }); var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; a.click(); },
  saveToHistory: function(role, content) { var h = JSON.parse(localStorage.getItem('nebula_chat_history') || '[]'); h.push({ role: role, content: content, sessionId: this.sessionId, time: new Date().toISOString() }); if (h.length > 500) h.splice(0, h.length - 500); localStorage.setItem('nebula_chat_history', JSON.stringify(h)); },
  autoResize: function() { if (!this.input) return; this.input.style.height = 'auto'; this.input.style.height = Math.min(this.input.scrollHeight, 130) + 'px'; },
  scrollToBottom: function() { if (this.messagesContainer) this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight; },
  updateWordCount: function() { var c = this.input ? this.input.value.length : 0; var el = document.getElementById('word-count'); if (el) el.textContent = c + ' chars'; }
};