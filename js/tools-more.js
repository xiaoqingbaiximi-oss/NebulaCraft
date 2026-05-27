var ToolsMore = {
  init: function() {
    if (typeof Tools === 'undefined') { setTimeout(function() { ToolsMore.init(); }, 300); return; }

    var configs = {
      '每日运势': { icon: '🔮', desc: '查看今日运势', keywords: '运势' },
      '密码本': { icon: '🔐', desc: '加密存储密码', keywords: '密码' },
      '文本对比': { icon: '📊', desc: '文本差异比较', keywords: '对比' },
      '正则测试': { icon: '🔍', desc: '正则表达式测试', keywords: '正则' },
      '番茄钟': { icon: '🍅', desc: '番茄工作法计时', keywords: '番茄' },
      '习惯打卡': { icon: '✅', desc: '每日习惯追踪', keywords: '习惯' },
      '颜色拾取器': { icon: '🎨', desc: '取色+调色板', keywords: '颜色' },
      '图片裁剪': { icon: '✂️', desc: '图片裁剪调整', keywords: '裁剪' },
      'SVG预览': { icon: '🖼️', desc: 'SVG实时预览', keywords: 'svg' }
    };

    for (var k in configs) { Tools.toolConfigs[k] = configs[k]; }
    Tools.categories['🎯 扩展'] = Object.keys(configs);

    var orig = Tools.openTool;
    var fns = {
      '每日运势': this._fortune, '密码本': this._vault, '文本对比': this._diff,
      '正则测试': this._regex, '番茄钟': this._pomodoro, '习惯打卡': this._habit,
      '颜色拾取器': this._color, '图片裁剪': this._crop, 'SVG预览': this._svg
    };
    var self = this;
    
    Tools.openTool = function(name) {
      if (fns[name]) {
        Tools.addToRecent(name);
        UI.switchView('tools');
        fns[name].call(self);
        return;
      }
      orig.call(Tools, name);
    };
  },

  _el: function() { return document.getElementById('tools-result'); },
  _esc: function(s) { var d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; },

  _fortune: function() {
    var el = this._el(); if (!el) return;
    var signs = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座','天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座'];
    var all = [['大吉','⭐⭐⭐⭐⭐','诸事顺遂'],['吉','⭐⭐⭐⭐','保持积极'],['中吉','⭐⭐⭐','适合学习'],['小吉','⭐⭐','略有波折'],['凶','⭐','谨慎行事']];
    var f = all[Math.floor(Math.random()*5)];
    el.innerHTML = '<div class="result-card"><h3>🔮 每日运势</h3><div class="result-content" style="text-align:center;line-height:2.2"><p>星座: <strong>'+signs[Math.floor(Math.random()*12)]+'</strong></p><p>运势: <strong>'+f[0]+' '+f[1]+'</strong></p><p>幸运数字: <strong>'+Math.floor(Math.random()*99+1)+'</strong></p><p style="color:var(--text2)">💡 '+f[2]+'</p></div><button class="btn-sm primary" onclick="ToolsMore._fortune()">🔄 换一个</button></div>';
  },

  _vault: function() {
    var el = this._el(); if (!el) return;
    var data = {}; try { data = JSON.parse(localStorage.getItem('nv')||'{}'); } catch(e) {}
    var keys = Object.keys(data), html = '', self = this;
    for (var i=0;i<keys.length;i++) {
      var s = keys[i];
      html += '<div style="display:flex;justify-content:space-between;padding:10px;background:var(--bg);border-radius:8px;margin-bottom:6px"><span><strong>'+self._esc(s)+'</strong> ('+self._esc(data[s].u||'')+')</span><span><button class="btn-sm" onclick="ToolsMore._vc(\''+s+'\')">📋</button><button class="btn-sm" onclick="ToolsMore._vd(\''+s+'\')">🗑️</button></span></div>';
    }
    el.innerHTML = '<div class="result-card"><h3>🔐 密码本</h3><div class="result-content">'+(html||'<p style="color:var(--text2);text-align:center;padding:20px">密码本为空</p>')+'</div><div class="result-actions" style="margin-top:12px;gap:6px;flex-wrap:wrap"><input id="vs" placeholder="站点" style="flex:1;min-width:60px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit"><input id="vu" placeholder="用户名" style="flex:1;min-width:60px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit"><input id="vp" type="password" placeholder="密码" style="flex:1;min-width:60px;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit"><button class="btn-sm primary" onclick="ToolsMore._va()">➕</button></div></div>';
  },
  _va: function() { var s=document.getElementById('vs').value.trim(),u=document.getElementById('vu').value.trim(),p=document.getElementById('vp').value; if(!s||!p){App.toast('请填写站点和密码','error');return;} var d={};try{d=JSON.parse(localStorage.getItem('nv')||'{}');}catch(e){} d[s]={u:u,p:btoa(p),t:new Date().toLocaleString('zh-CN')}; localStorage.setItem('nv',JSON.stringify(d)); App.toast('已保存','success'); this._vault(); },
  _vc: function(s) { var d={};try{d=JSON.parse(localStorage.getItem('nv')||'{}');}catch(e){} if(d[s]){navigator.clipboard.writeText(atob(d[s].p||''));App.toast('已复制','success');} },
  _vd: function(s) { var d={};try{d=JSON.parse(localStorage.getItem('nv')||'{}');}catch(e){} delete d[s]; localStorage.setItem('nv',JSON.stringify(d)); App.toast('已删除','info'); this._vault(); },

  _diff: function() {
    var el = this._el(); if (!el) return;
    el.innerHTML = '<div class="result-card"><h3>📊 文本对比</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px"><div><div style="font-size:.8rem;color:var(--text2)">文本A</div><textarea id="d1" rows="6" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;box-sizing:border-box"></textarea></div><div><div style="font-size:.8rem;color:var(--text2)">文本B</div><textarea id="d2" rows="6" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;box-sizing:border-box"></textarea></div></div><button class="btn-sm primary" onclick="ToolsMore._df()">🔍 对比</button><div id="do" class="result-content" style="margin-top:12px;display:none;font-family:monospace;font-size:.85rem;line-height:1.8"></div></div>';
  },
  _df: function() { var a=(document.getElementById('d1').value||'').split('\n'),b=(document.getElementById('d2').value||'').split('\n'),m=Math.max(a.length,b.length),r=[],self=this;for(var i=0;i<m;i++){var la=i<a.length?a[i]:'',lb=i<b.length?b[i]:'';if(la===lb)r.push('<span style="color:var(--text2)">  '+self._esc(la||'(空)')+'</span>');else{if(la)r.push('<span style="color:var(--danger);background:rgba(239,68,68,0.1)">- '+self._esc(la)+'</span>');if(lb)r.push('<span style="color:var(--success);background:rgba(16,185,129,0.1)">+ '+self._esc(lb)+'</span>');}}document.getElementById('do').style.display='block';document.getElementById('do').innerHTML=r.join('\n');},

  _regex: function() {
    var el = this._el(); if (!el) return;
    el.innerHTML = '<div class="result-card"><h3>🔍 正则测试</h3><input id="rp" placeholder="正则表达式" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;margin-bottom:8px;box-sizing:border-box"><textarea id="rt" rows="4" placeholder="测试文本" style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;box-sizing:border-box"></textarea><div style="margin-top:12px"><button class="btn-sm primary" onclick="ToolsMore._rx()">🔍 匹配</button><label style="font-size:.8rem;margin-left:8px"><input type="checkbox" id="rg" checked>全局</label><label style="font-size:.8rem"><input type="checkbox" id="ri">忽略大小写</label></div><div id="ro" class="result-content" style="margin-top:12px;display:none;font-family:monospace;font-size:.85rem"></div></div>';
  },
  _rx: function() { var p=document.getElementById('rp').value,t=document.getElementById('rt').value,g=document.getElementById('rg').checked,i=document.getElementById('ri').checked,o=document.getElementById('ro');if(!p){o.style.display='block';o.innerHTML='<span style="color:var(--danger)">请输入正则</span>';return;}try{var re=new RegExp(p,(g?'g':'')+(i?'i':'')),m=t.match(re);o.style.display='block';if(m){var h='✅ 匹配 '+m.length+' 个:<br>';for(var j=0;j<m.length;j++)h+='<span style="background:rgba(108,92,231,0.2);padding:2px 6px;border-radius:4px;margin:2px;display:inline-block">'+ToolsMore._esc(m[j])+'</span><br>';o.innerHTML=h;}else{o.innerHTML='⚠️ 无匹配';}}catch(e){o.style.display='block';o.innerHTML='<span style="color:var(--danger)">错误: '+ToolsMore._esc(e.message)+'</span>';}},

  _timer: null, _min: 25, _sec: 0, _run: false,
  _pomodoro: function() {
    var el = this._el(); if (!el) return;
    this._min=25;this._sec=0;this._run=false;if(this._timer)clearInterval(this._timer);
    el.innerHTML = '<div class="result-card" style="text-align:center"><h3>🍅 番茄钟</h3><div class="result-content"><div id="pd" style="font-size:4rem;font-weight:700;font-family:monospace;padding:30px">25:00</div><div id="ps" style="color:var(--text2);margin-bottom:12px">点击开始</div></div><div style="justify-content:center;gap:8px;display:flex"><button class="btn-sm primary" id="pst" onclick="ToolsMore._pst()">▶️ 开始</button><button class="btn-sm" id="pp" onclick="ToolsMore._pp()" style="display:none">⏸️ 暂停</button><button class="btn-sm" onclick="ToolsMore._prs()">🔄 重置</button></div></div>';
  },
  _pst: function() { if(this._run)return;this._run=true;document.getElementById('pst').style.display='none';document.getElementById('pp').style.display='inline-block';document.getElementById('ps').textContent='专注中...';var self=this;this._timer=setInterval(function(){if(self._sec===0){if(self._min===0){self._pc();return;}self._min--;self._sec=59;}else{self._sec--;}document.getElementById('pd').textContent=String(self._min).padStart(2,'0')+':'+String(self._sec).padStart(2,'0');},1000);},
  _pp: function() { this._run=false;if(this._timer)clearInterval(this._timer);document.getElementById('pst').style.display='inline-block';document.getElementById('pp').style.display='none';document.getElementById('ps').textContent='已暂停'; },
  _prs: function() { this._run=false;if(this._timer)clearInterval(this._timer);this._min=25;this._sec=0;document.getElementById('pd').textContent='25:00';document.getElementById('pst').style.display='inline-block';document.getElementById('pp').style.display='none';document.getElementById('ps').textContent='点击开始'; },
  _pc: function() { if(this._timer)clearInterval(this._timer);this._run=false;document.getElementById('pd').textContent='00:00';document.getElementById('pst').style.display='inline-block';document.getElementById('pp').style.display='none';document.getElementById('ps').textContent='🎉 完成！';App.toast('番茄钟完成！','success');try{var c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator();o.frequency.value=800;o.connect(c.destination);o.start();setTimeout(function(){o.stop();},200);}catch(e){}},

  _habit: function() {
    var el = this._el(); if (!el) return;
    var h=[];try{h=JSON.parse(localStorage.getItem('nh')||'[]');}catch(e){}
    var t=new Date().toISOString().split('T')[0],html='',self=this;
    for(var i=0;i<h.length;i++){
      var d=h[i].d&&h[i].d.indexOf(t)!==-1,s=self._hs(h[i].d||[]);
      html+='<div style="display:flex;align-items:center;gap:12px;padding:12px;background:var(--bg);border-radius:8px;margin-bottom:6px"><button onclick="ToolsMore._th('+i+')" style="width:36px;height:36px;border-radius:50%;border:2px solid '+(d?'var(--success)':'var(--border)')+';background:'+(d?'var(--success)':'transparent')+';color:#fff;font-size:1.2rem;cursor:pointer;flex-shrink:0">'+(d?'✓':'')+'</button><div style="flex:1"><strong>'+self._esc(h[i].n)+'</strong><div style="font-size:.75rem;color:var(--text2)">🔥 '+s+' 天</div></div><button onclick="ToolsMore._dh('+i+')" style="background:none;border:none;cursor:pointer;font-size:1.1rem">🗑️</button></div>';
    }
    el.innerHTML='<div class="result-card"><h3>✅ 习惯打卡</h3><div class="result-content">'+(html||'<p style="color:var(--text2);text-align:center;padding:20px">还没有习惯 ✨</p>')+'</div><div style="margin-top:12px;display:flex;gap:8px"><input id="nhi" placeholder="新习惯" style="flex:1;padding:8px 12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit" onkeydown="if(event.key===\'Enter\')ToolsMore._ah()"><button class="btn-sm primary" onclick="ToolsMore._ah()">➕</button></div></div>';
  },
  _ah: function() { var n=document.getElementById('nhi').value.trim();if(!n)return;var h=[];try{h=JSON.parse(localStorage.getItem('nh')||'[]');}catch(e){}h.push({n:n,d:[]});localStorage.setItem('nh',JSON.stringify(h));App.toast('已添加','success');this._habit();},
  _th: function(i) { var h=[];try{h=JSON.parse(localStorage.getItem('nh')||'[]');}catch(e){}if(!h[i])return;var t=new Date().toISOString().split('T')[0],d=h[i].d||[],idx=d.indexOf(t);if(idx>-1)d.splice(idx,1);else d.push(t);h[i].d=d;localStorage.setItem('nh',JSON.stringify(h));this._habit();},
  _dh: function(i) { var h=[];try{h=JSON.parse(localStorage.getItem('nh')||'[]');}catch(e){}h.splice(i,1);localStorage.setItem('nh',JSON.stringify(h));App.toast('已删除','info');this._habit();},
  _hs: function(d) { if(!d||!d.length)return 0;d=d.slice().sort().reverse();var s=1;for(var i=0;i<d.length-1;i++){if(Math.round((new Date(d[i])-new Date(d[i+1]))/86400000)===1)s++;else break;}return s;},

  _color: function() {
    var el = this._el(); if (!el) return;
    el.innerHTML = '<div class="result-card" style="text-align:center"><h3>🎨 颜色拾取器</h3><div class="result-content"><input type="color" id="cp" value="#6c5ce7" style="width:120px;height:120px;border:none;border-radius:50%;cursor:pointer;margin:20px"><div style="font-family:monospace;font-size:1.05rem;line-height:2"><p>HEX: <strong id="chx">#6c5ce7</strong></p><p>RGB: <strong id="crgb">108,92,231</strong></p></div><div id="cpr" style="width:100%;height:60px;border-radius:12px;background:#6c5ce7;margin-top:12px"></div></div><button class="btn-sm primary" onclick="ToolsMore._cc()" style="margin-top:12px">📋 复制</button></div>';
    document.getElementById('cp').oninput=function(){var h=this.value;document.getElementById('chx').textContent=h;document.getElementById('crgb').textContent=parseInt(h.slice(1,3),16)+','+parseInt(h.slice(3,5),16)+','+parseInt(h.slice(5,7),16);document.getElementById('cpr').style.background=h;};
  },
  _cc: function() { var h=document.getElementById('chx').textContent; if(h)navigator.clipboard.writeText(h).then(function(){App.toast('已复制','success');}); },

  _svg: function() {
    var el = this._el(); if (!el) return;
    el.innerHTML = '<div class="result-card"><h3>🖼️ SVG预览</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;min-height:300px"><div><textarea id="svi" placeholder=\'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="#6c5ce7"/></svg>\' style="width:100%;height:280px;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:monospace;resize:vertical;box-sizing:border-box"></textarea></div><div id="svp" style="height:280px;display:flex;align-items:center;justify-content:center;background:var(--bg);border-radius:8px;border:1px solid var(--border);padding:16px;overflow:hidden;box-sizing:border-box"></div></div><div style="margin-top:12px;display:flex;gap:8px"><button class="btn-sm primary" onclick="ToolsMore._csv()">📋 复制</button><button class="btn-sm" onclick="ToolsMore._dsv()">💾 下载</button></div></div>';
    document.getElementById('svi').oninput=function(){document.getElementById('svp').innerHTML=this.value||'';};
  },
  _csv: function() { var c=document.getElementById('svi').value;if(c)navigator.clipboard.writeText(c); },
  _dsv: function() { var c=document.getElementById('svi').value;if(c){var a=document.createElement('a');a.download='icon.svg';a.href=URL.createObjectURL(new Blob([c],{type:'image/svg+xml'}));a.click();}},

  _crop: function() {
    var el = this._el(); if (!el) return;
    this._img=null;this._cvs=null;
    el.innerHTML = '<div class="result-card"><h3>✂️ 图片裁剪</h3><div class="result-content" style="text-align:center"><input type="file" id="cfi" accept="image/*" style="padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border)"><div id="cpp" style="margin-top:16px;max-height:400px"></div></div><div style="margin-top:12px;display:none;gap:8px" id="cpa"><button class="btn-sm primary" onclick="ToolsMore._dcr()">✂️ 裁剪</button><button class="btn-sm" onclick="ToolsMore._crst()">↩️ 重置</button><button class="btn-sm" onclick="ToolsMore._dcrd()">💾 下载</button></div><canvas id="ccv" style="display:none"></canvas></div>';
    var self=this;document.getElementById('cfi').onchange=function(e){var f=e.target.files[0];if(!f)return;var r=new FileReader();r.onload=function(ev){var img=new Image();img.onload=function(){document.getElementById('cpp').innerHTML='<img src="'+ev.target.result+'" style="max-width:100%;max-height:350px;border-radius:8px">';document.getElementById('cpa').style.display='flex';var c=document.getElementById('ccv');c.width=img.width;c.height=img.height;c.getContext('2d').drawImage(img,0,0);self._img=img;};img.src=ev.target.result;};r.readAsDataURL(f);};
  },
  _dcr: function() { var c=document.getElementById('ccv');if(!c||!this._img)return;var w=c.width,h=c.height,t=Math.floor(h*.1),b=Math.floor(h*.9),nc=document.createElement('canvas');nc.width=w;nc.height=b-t;nc.getContext('2d').drawImage(c,0,t,w,b-t,0,0,w,b-t);document.getElementById('cpp').innerHTML='<img src="'+nc.toDataURL()+'" style="max-width:100%;max-height:350px;border-radius:8px">';this._cvs=nc;App.toast('裁剪完成','success');},
  _crst: function() { if(!this._img)return;var c=document.getElementById('ccv');c.getContext('2d').drawImage(this._img,0,0);document.getElementById('cpp').innerHTML='<img src="'+c.toDataURL()+'" style="max-width:100%;max-height:350px;border-radius:8px">';},
  _dcrd: function() { if(!this._cvs){App.toast('请先裁剪','error');return;}var a=document.createElement('a');a.download='cropped.png';a.href=this._cvs.toDataURL();a.click();}
};