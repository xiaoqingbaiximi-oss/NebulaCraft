var MobileNative = {
  init: function() {
    this._detectPlatform();
    this._bindNativeFeatures();
  },

  _detectPlatform: function() {
    var ua = navigator.userAgent;
    this.isIOS = /iPhone|iPad|iPod/.test(ua);
    this.isAndroid = /Android/.test(ua);
    this.isPWA = window.matchMedia('(display-mode: standalone)').matches;

    if (this.isPWA) {
      document.body.classList.add('pwa-mode');
    }
  },

  _bindNativeFeatures: function() {
    // 推送通知
    if ('PushManager' in window) {
      this._registerPush();
    }

    // 桌面小组件（通过 Web App Manifest）
    if (this.isPWA) {
      this._enableWidgets();
    }

    // 手表伴侣（通过 Bluetooth API）
    if ('bluetooth' in navigator) {
      console.log('蓝牙可用 - 可连接手表设备');
    }
  },

  _registerPush: function() {
    var self = this;
    navigator.serviceWorker.ready.then(function(reg) {
      reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: self._urlBase64ToUint8Array(
          'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U'
        )
      }).then(function(sub) {
        console.log('推送订阅成功');
      }).catch(function(e) {
        console.log('推送订阅失败:', e);
      });
    });
  },

  _enableWidgets: function() {
    // 通过 Web Periodic Background Sync 模拟小组件更新
    if ('periodicSync' in navigator.serviceWorker) {
      console.log('后台同步可用');
    }
  },

  _urlBase64ToUint8Array: function(base64String) {
    var padding = '='.repeat((4 - base64String.length % 4) % 4);
    var base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    var rawData = window.atob(base64);
    var outputArray = new Uint8Array(rawData.length);
    for (var i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  },

  shareViaNative: function(text) {
    if (navigator.share) {
      navigator.share({
        title: 'NebulaCraft',
        text: text,
      }).catch(function() {});
    }
  },

  addToHomeScreen: function() {
    if (window.deferredPrompt) {
      window.deferredPrompt.prompt();
      window.deferredPrompt.userChoice.then(function(result) {
        console.log(result.outcome);
      });
    }
  }
};