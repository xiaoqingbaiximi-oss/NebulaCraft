var AIEnhance = {
  init: function() {
    this._hijackChat();
    this._bindIntentPrediction();
  },

  _hijackChat: function() {
    var self = this;
    var originalSend = Chat.send;

    Chat.send = function() {
      var text = Chat.input.value.trim();
      if (!text) { originalSend.call(Chat); return; }

      // 检测 @知识库 自动检索
      if (text.includes('@知识库')) {
        var query = text.replace('@知识库', '').trim();
        if (query) {
          self._injectKnowledge(query, function() {
            originalSend.call(Chat);
          });
          return;
        }
      }

      // 检测 @搜索 自动联网
      if (text.includes('@搜索')) {
        var q = text.replace('@搜索', '').trim();
        Chat.input.value = '搜索 ' + q;
        originalSend.call(Chat);
        return;
      }

      // 检测 @图片 自动生成
      if (text.includes('@图片')) {
        var prompt = text.replace('@图片', '').trim();
        if (prompt) {
          Tools.openTool('AI 图像生成');
          setTimeout(function() {
            var inp = document.getElementById('sd-prompt');
            if (inp) { inp.value = prompt; Tools._sdGenerate(); }
          }, 500);
          return;
        }
      }

      // 情绪分析
      self._analyzeSentiment(text);

      originalSend.call(Chat);
    };
  },

  _injectKnowledge: function(query, callback) {
    fetch('/api/knowledge', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: 'search', collection: Knowledge.currentCollection, query: query, top_k: 3}),
      signal: AbortSignal.timeout(8000)
    }).then(function(r){return r.json();}).then(function(d){
      if (d.ok && d.results && d.results.length > 0) {
        var ctx = d.results.map(function(r, i) {
          return '[参考' + (i+1) + '] ' + r.text.slice(0, 300);
        }).join('\n\n');
        Chat.input.value = '基于以下参考资料回答问题：\n\n' + ctx + '\n\n问题：' + query;
      }
      callback();
    }).catch(function(){ callback(); });
  },

  _bindIntentPrediction: function() {
    var input = document.getElementById('chat-input');
    if (!input) return;
    var self = this;

    var timer;
    input.addEventListener('input', function() {
      clearTimeout(timer);
      var text = input.value.trim();
      if (!text || text.length < 3) { self._hidePrediction(); return; }

      timer = setTimeout(function() {
        self._predict(text);
      }, 500);
    });
  },

  _predict: function(text) {
    var predictions = [];
    var lower = text.toLowerCase();

    if (/计算|bmi|房贷|折扣|数学|税率/.test(lower)) predictions.push({name: '万能计算器', icon: '🧮'});
    if (/密码|uuid|生成|验证码/.test(lower)) predictions.push({name: '密码生成', icon: '🔑'});
    if (/天气|气温/.test(lower)) predictions.push({name: '天气查询', icon: '🌤️'});
    if (/翻译|英文|日语|韩语/.test(lower)) predictions.push({name: '翻译', icon: '🌐'});
    if (/图片|绘图|画|生成图/.test(lower)) predictions.push({name: 'AI 图像生成', icon: '🎨'});
    if (/润色|改稿|简历|总结|演讲稿/.test(lower)) predictions.push({name: '智能指令', icon: '🧠'});

    if (predictions.length > 0) {
      this._showPrediction(predictions);
    } else {
      this._hidePrediction();
    }
  },

  _showPrediction: function(predictions) {
    var el = document.getElementById('ai-predictions');
    if (!el) {
      el = document.createElement('div');
      el.id = 'ai-predictions';
      el.style.cssText = 'position:absolute;bottom:100%;left:16px;right:16px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:8px;margin-bottom:4px;display:flex;gap:6px;flex-wrap:wrap;z-index:10;box-shadow:0 -4px 20px rgba(0,0,0,0.3)';
      var inputArea = document.querySelector('.input-area');
      if (inputArea) { inputArea.style.position = 'relative'; inputArea.appendChild(el); }
    }

    var self = this;
    el.innerHTML = '<span style="font-size:.7rem;color:var(--text2);width:100%">💡 试试这些工具:</span>' +
      predictions.map(function(p) {
        return '<span style="background:var(--accent-glow);padding:6px 12px;border-radius:16px;font-size:.8rem;cursor:pointer" onclick="AIEnhance._useTool(\'' + p.name + '\')">' + p.icon + ' ' + p.name + '</span>';
      }).join('');
    el.style.display = 'flex';
  },

  _hidePrediction: function() {
    var el = document.getElementById('ai-predictions');
    if (el) el.style.display = 'none';
  },

  _useTool: function(name) {
    this._hidePrediction();
    if (name === '智能指令') { App.showCheatsheet(); return; }
    if (typeof Tools !== 'undefined') Tools.openTool(name);
  },

  _analyzeSentiment: function(text) {
    var positive = ['开心','高兴','喜欢','好','棒','厉害','感谢','谢谢','爱','不错','完美','优秀','赞'];
    var negative = ['难过','生气','烦','糟糕','差','垃圾','失败','讨厌','恨','不行','问题'];
    var score = 0;
    positive.forEach(function(w) { if (text.includes(w)) score++; });
    negative.forEach(function(w) { if (text.includes(w)) score--; });

    if (score > 2) {
      this._showEmoji('😊');
    } else if (score < -2) {
      this._showEmoji('😢');
    }
  },

  _showEmoji: function(emoji) {
    var el = document.getElementById('ai-emoji');
    if (!el) {
      el = document.createElement('div');
      el.id = 'ai-emoji';
      el.style.cssText = 'position:fixed;bottom:100px;right:20px;font-size:2rem;animation:floatUp 2s ease forwards;pointer-events:none;z-index:100';
      document.body.appendChild(el);
    }
    el.textContent = emoji;
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'floatUp 2s ease forwards';

    var style = document.createElement('style');
    style.textContent = '@keyframes floatUp { 0% { opacity:1; transform:translateY(0); } 100% { opacity:0; transform:translateY(-80px); } }';
    if (!document.querySelector('#floatUpStyle')) {
      style.id = 'floatUpStyle';
      document.head.appendChild(style);
    }
  }
};