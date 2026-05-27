var Knowledge = {
  currentCollection: 'default',

  init: function() {
    var self = this;
    setTimeout(function() { self._registerTools(); }, 600);
  },

  _registerTools: function() {
    if (typeof Tools === 'undefined') { var self = this; setTimeout(function() { self._registerTools(); }, 500); return; }
    console.log('Knowledge: register tools');

    Tools.toolConfigs['Knowledge Base'] = { icon: '📚', desc: 'Manage knowledge base', keywords: 'knowledge RAG' };
    if (!Tools.categories['🧠 AI']) Tools.categories['🧠 AI'] = [];
    if (Tools.categories['🧠 AI'].indexOf('Knowledge Base') === -1) Tools.categories['🧠 AI'].push('Knowledge Base');
    Tools.toolConfigs['Agent Tasks'] = { icon: '🤖', desc: 'AI multi-step tasks', keywords: 'agent auto' };
    if (Tools.categories['🧠 AI'].indexOf('Agent Tasks') === -1) Tools.categories['🧠 AI'].push('Agent Tasks');
    Tools.toolConfigs['Plugins'] = { icon: '🔌', desc: 'Manage plugins', keywords: 'plugin' };
    if (Tools.categories['🧠 AI'].indexOf('Plugins') === -1) Tools.categories['🧠 AI'].push('Plugins');

    if (UI.currentView === 'tools') Tools.render();

    var orig = Tools.openTool;
    var self = this;
    Tools.openTool = function(name) {
      if (name === 'Knowledge Base') { Tools.addToRecent(name); UI.switchView('tools'); self.showKB(); return; }
      if (name === 'Agent Tasks') { Tools.addToRecent(name); UI.switchView('tools'); self.showAgent(); return; }
      if (name === 'Plugins') { Tools.addToRecent(name); UI.switchView('tools'); self.showPlugins(); return; }
      orig.call(Tools, name);
    };
  },

  _esc: function(s) { var d = document.createElement('div'); d.textContent = String(s||''); return d.innerHTML; },
  _close: function() { return '<button onclick="Tools.closeTool()" style="background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text2);padding:0 8px">X</button>'; },

  showKB: function() {
    var el = document.getElementById('tools-result'); if (!el) return;
    var self = this;
    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>📚 Knowledge Base</h3>'+self._close()+'</div><div class="result-content"><p>Loading...</p></div></div>';

    fetch('/api/knowledge', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'list_collections'}), signal:AbortSignal.timeout(8000) })
      .then(function(r){return r.json();}).then(function(d){
        var cols = d.ok ? (d.collections||[]) : [];
        var html = '<div style="display:flex;gap:12px;margin-bottom:16px"><div style="flex:1;text-align:center;padding:12px;background:var(--bg);border-radius:8px"><div style="font-size:1.5rem;font-weight:700">'+cols.length+'</div><div style="font-size:.8rem;color:var(--text2)">Collections</div></div></div>';
        html += '<h4>Collections</h4>';
        if (cols.length === 0) { html += '<p style="color:var(--text2)">No collections yet</p>'; }
        else { cols.forEach(function(c){ html += '<div style="padding:10px;background:var(--bg);border-radius:8px;margin-bottom:6px"><strong>'+self._esc(c.name)+'</strong> <span style="font-size:.8rem;color:var(--text2)">'+c.documents+' docs</span></div>'; }); }
        html += '<div style="margin-top:12px"><input id="kb-search" placeholder="Search knowledge base..." style="width:100%;padding:10px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit;box-sizing:border-box" onkeydown="if(event.key===\'Enter\')Knowledge._search()"><div id="kb-results" style="margin-top:8px"></div></div>';
        html += '<div style="margin-top:12px;display:flex;gap:8px"><input id="new-col-name" placeholder="New collection" style="flex:1;padding:8px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit"><button class="btn-sm primary" onclick="Knowledge._createCol()">+ Create</button></div>';
        el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>📚 Knowledge Base</h3>'+self._close()+'</div><div class="result-content">'+html+'</div></div>';
      }).catch(function(){ el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>📚 Knowledge Base</h3>'+self._close()+'</div><div class="result-content"><p style="color:var(--danger)">Failed to load. Is backend running?</p></div></div>'; });
  },

  _createCol: function() { var n=document.getElementById('new-col-name').value.trim(); if(!n)return; var self=this; fetch('/api/knowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'create_collection',name:n}),signal:AbortSignal.timeout(8000)}).then(function(r){return r.json();}).then(function(d){ App.toast(d.ok?'Created':'Failed',d.ok?'success':'error'); if(d.ok)self.showKB(); }); },
  _search: function() { var q=document.getElementById('kb-search').value.trim(); if(!q)return; var out=document.getElementById('kb-results'); if(out)out.innerHTML='<p>Searching...</p>'; var self=this; fetch('/api/knowledge',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'search',collection:this.currentCollection,query:q,top_k:5}),signal:AbortSignal.timeout(10000)}).then(function(r){return r.json();}).then(function(d){ if(!out)return; if(!d.ok||!d.results||!d.results.length){out.innerHTML='<p style="color:var(--text2)">No results</p>';return;} var h=''; d.results.forEach(function(r){h+='<div style="padding:10px;background:var(--bg);border-radius:6px;margin-bottom:4px"><strong>'+self._esc(r.title)+'</strong><p style="font-size:.85rem;color:var(--text2)">'+self._esc(r.text.slice(0,200))+'</p></div>';}); out.innerHTML=h; }).catch(function(){ if(out)out.innerHTML='<p style="color:var(--danger)">Search failed</p>'; }); },

  showAgent: function() {
    var el = document.getElementById('tools-result'); if (!el) return;
    var self = this;
    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>🤖 Agent Tasks</h3>'+self._close()+'</div><div class="result-content"><textarea id="agent-input" rows="3" placeholder="Describe your task..." style="width:100%;padding:12px;border-radius:8px;background:var(--bg);color:var(--text);border:1px solid var(--border);font-family:inherit;resize:vertical;min-height:80px;box-sizing:border-box"></textarea></div><button class="btn-sm primary" onclick="Knowledge._runAgent()" style="margin-top:8px">Run</button><div id="agent-output" style="margin-top:12px"></div></div>';
  },
  _runAgent: function() { var t=document.getElementById('agent-input').value.trim(); if(!t)return; var out=document.getElementById('agent-output'); if(out)out.innerHTML='<p>Running...</p>'; fetch('/api/agent',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t}),signal:AbortSignal.timeout(120000)}).then(function(r){return r.json();}).then(function(d){ if(!out)return; if(!d.ok){out.innerHTML='<p style="color:var(--danger)">'+d.error+'</p>';return;} out.innerHTML='<p style="color:var(--success)">Done: '+d.steps_count+' steps</p><pre style="background:var(--bg);padding:12px;border-radius:8px;max-height:400px;overflow-y:auto;font-size:.85rem">'+JSON.stringify(d.steps,null,2)+'</pre>'; }).catch(function(e){ if(out)out.innerHTML='<p style="color:var(--danger)">Failed: '+e.message+'</p>'; }); },

  showPlugins: function() {
    var el = document.getElementById('tools-result'); if (!el) return;
    var self = this;
    el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>🔌 Plugins</h3>'+self._close()+'</div><div class="result-content"><p>Loading...</p></div></div>';

    fetch('/api/plugin', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'list'}), signal:AbortSignal.timeout(8000) })
      .then(function(r){return r.json();}).then(function(d){
        var plugins = d.ok ? (d.plugins||[]) : [];
        var html = '';
        if (plugins.length === 0) { html += '<p style="color:var(--text2)">No plugins installed</p>'; }
        else { plugins.forEach(function(p){ html += '<div style="display:flex;justify-content:space-between;padding:10px;background:var(--bg);border-radius:8px;margin-bottom:6px"><div><strong>'+self._esc(p.name)+'</strong> <span style="font-size:.8rem;color:var(--text2)">v'+p.version+'</span></div><span>'+(p.enabled?'Active':'Disabled')+'</span></div>'; }); }
        el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>🔌 Plugins</h3>'+self._close()+'</div><div class="result-content">'+html+'</div></div>';
      }).catch(function(){ el.innerHTML = '<div class="result-card"><div style="display:flex;justify-content:space-between"><h3>🔌 Plugins</h3>'+self._close()+'</div><div class="result-content"><p style="color:var(--danger)">Failed to load</p></div></div>'; });
  }
};