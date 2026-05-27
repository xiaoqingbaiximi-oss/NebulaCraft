var Voice = {
  listening: false,
  recognition: null,

  init: function() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SR();
      this.recognition.lang = 'zh-CN';
      this.recognition.interimResults = true;
      this.recognition.continuous = false;

      var self = this;
      this.recognition.onresult = function(e) {
        var text = '';
        for (var i = 0; i < e.results.length; i++) {
          text += e.results[i][0].transcript;
        }
        var input = document.getElementById('chat-input');
        if (input) {
          input.value = text;
          if (e.results[0].isFinal) {
            input.focus();
            Chat.autoResize();
          }
        }
      };

      this.recognition.onerror = function(e) {
        self.listening = false;
        self._updateBtn();
        if (e.error === 'not-allowed') {
          App.toast('请允许麦克风权限', 'error');
        }
      };

      this.recognition.onend = function() {
        self.listening = false;
        self._updateBtn();
      };
    }
  },

  toggle: function() {
    if (!this.recognition) {
      App.toast('浏览器不支持语音识别', 'error');
      return;
    }

    if (this.listening) {
      this.recognition.stop();
      this.listening = false;
    } else {
      try {
        this.recognition.start();
        this.listening = true;
        App.toast('🎤 正在聆听...', 'info');
      } catch(e) {
        this.listening = false;
      }
    }
    this._updateBtn();
  },

  _updateBtn: function() {
    var btn = document.querySelector('[onclick="Voice.toggle()"]');
    if (btn) {
      btn.style.color = this.listening ? '#ef4444' : '';
      btn.title = this.listening ? '停止' : '语音输入';
    }
  }
};