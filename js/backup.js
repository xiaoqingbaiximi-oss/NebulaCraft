var Backup = {
  init: function() {
    // 每天自动备份一次
    this._schedule();
  },

  _schedule: function() {
    var lastBackup = localStorage.getItem('nebula_last_backup');
    var today = new Date().toDateString();

    if (lastBackup !== today) {
      // 延迟执行，等页面加载完
      setTimeout(function() { Backup.doBackup(); }, 10000);
    }

    // 每小时检查一次
    setInterval(function() {
      var now = new Date().toDateString();
      if (localStorage.getItem('nebula_last_backup') !== now) {
        Backup.doBackup();
      }
    }, 3600000);
  },

  doBackup: function() {
    var data = {};
    var keys = ['nebula_chat_history', 'nebula_settings', 'nebula_habits', 'nebula_local_notes', 'nv', 'nf', 'nrt', 'nebula_templates'];
    var totalSize = 0;

    keys.forEach(function(k) {
      var v = localStorage.getItem(k);
      if (v) {
        data[k] = v;
        totalSize += v.length;
      }
    });

    var backup = {
      time: new Date().toISOString(),
      version: '7.0.0',
      data: data,
    };

    try {
      localStorage.setItem('nebula_backup', JSON.stringify(backup));
      localStorage.setItem('nebula_last_backup', new Date().toDateString());
      console.log('✅ 自动备份完成 (' + (totalSize / 1024).toFixed(1) + ' KB)');
    } catch(e) {
      console.warn('备份失败:', e.message);
    }
  },

  restore: function() {
    try {
      var backup = JSON.parse(localStorage.getItem('nebula_backup') || '{}');
      if (!backup.data) {
        App.toast('没有可恢复的备份', 'error');
        return;
      }

      if (!confirm('确定恢复备份？当前数据将被覆盖。\n备份时间: ' + new Date(backup.time).toLocaleString('zh-CN'))) return;

      Object.keys(backup.data).forEach(function(k) {
        localStorage.setItem(k, backup.data[k]);
      });

      App.toast('恢复完成，请刷新页面', 'success');
      setTimeout(function() { location.reload(); }, 1500);
    } catch(e) {
      App.toast('恢复失败', 'error');
    }
  },

  exportAll: function() {
    var data = {};
    for (var i = 0; i < localStorage.length; i++) {
      var key = localStorage.key(i);
      if (key.startsWith('nebula_') || key === 'nv' || key === 'nh' || key === 'nf' || key === 'nrt') {
        data[key] = localStorage.getItem(key);
      }
    }

    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'nebulacraft-backup-' + new Date().toISOString().split('T')[0] + '.json';
    a.click();
    App.toast('已导出备份文件', 'success');
  },

  importAll: function() {
    var input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = function(e) {
      var file = e.target.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function(ev) {
        try {
          var data = JSON.parse(ev.target.result);
          var count = 0;
          Object.keys(data).forEach(function(k) {
            localStorage.setItem(k, data[k]);
            count++;
          });
          App.toast('已导入 ' + count + ' 项数据，刷新后生效', 'success');
          setTimeout(function() { location.reload(); }, 1500);
        } catch(e) {
          App.toast('导入失败: ' + e.message, 'error');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  }
};