var Notifications = {
  enabled: false,
  timerChecks: {},

  init: function() {
    this.requestPermission();
    this.startHabitReminder();
  },

  requestPermission: function() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(function(p) {
        Notifications.enabled = p === 'granted';
      });
    } else if ('Notification' in window && Notification.permission === 'granted') {
      this.enabled = true;
    }
  },

  send: function(title, body, icon) {
    icon = icon || '/static/icon-192.png';
    if (this.enabled) {
      new Notification(title, { body: body, icon: icon, badge: icon });
    }
    // 兜底：toast
    if (typeof App !== 'undefined') App.toast(title + ': ' + body, 'info');
  },

  startHabitReminder: function() {
    var self = this;
    // 每30分钟检查一次
    setInterval(function() {
      var now = new Date();
      if (now.getHours() === 9 && now.getMinutes() < 30) {
        self.send('习惯打卡提醒', '早上好！别忘了今天的习惯打卡 ✨');
      }
      if (now.getHours() === 21 && now.getMinutes() < 30) {
        self.send('习惯打卡提醒', '晚安前检查一下今天的习惯完成了吗？🌙');
      }
    }, 1800000);
  },

  pomodoroDone: function() {
    this.send('番茄钟完成', '休息一下吧！🍅', '/static/icon-192.png');
  },

  agentDone: function(summary) {
    this.send('Agent 任务完成', summary.slice(0, 100), '/static/icon-192.png');
  },

  knowledgeUpdated: function(count) {
    this.send('知识库更新', '已添加 ' + count + ' 个文档片段 📚', '/static/icon-192.png');
  }
};