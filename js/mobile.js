var Mobile = {
  isMobile: false,

  init: function() {
    this.isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || window.innerWidth < 768;
    if (this.isMobile) {
      document.body.classList.add('mobile');
      this.bindBottomNav();
    }
  },

  bindBottomNav: function() {
    var self = this;
    document.querySelectorAll('.bottom-nav-item').forEach(function(item) {
      item.addEventListener('click', function() {
        if (typeof UI !== 'undefined') UI.switchView(this.dataset.view);
        if (navigator.vibrate) navigator.vibrate(10);
      });
    });
  }
};