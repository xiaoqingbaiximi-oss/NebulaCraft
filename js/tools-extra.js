/* ==========================================
   TOOLS-EXTRA.JS — 扩展工具（二维码/颜色/时间戳/随机数）
   ========================================== */
const ToolsExtra = {

  // ===== 二维码生成 =====
  generateQR(text, size = 200) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');

    // 简单二维码模拟（实际项目用 qrcode.js 库）
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = '#000000';

    const modules = 25;
    const moduleSize = size / (modules + 8);
    const offset = moduleSize * 4;

    // 生成随机模块（模拟，实际用QR算法）
    const seed = this.hashString(text);
    for (let row = 0; row < modules; row++) {
      for (let col = 0; col < modules; col++) {
        if (this.shouldFill(row, col, seed)) {
          ctx.fillRect(
            offset + col * moduleSize,
            offset + row * moduleSize,
            moduleSize * 0.9,
            moduleSize * 0.9
          );
        }
      }
    }

    return canvas.toDataURL();
  },

  hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  },

  shouldFill(row, col, seed) {
    const pseudoRandom = ((row * 31 + col * 37 + seed) % 100);
    // 定位图案
    if (row < 7 && col < 7) return (row + col) % 2 === 0 || row === 0 || col === 0 || row === 6 || col === 6;
    if (row < 7 && col > 17) return (row + col) % 2 === 0 || row === 0 || col === 24 || row === 6 || col === 18;
    if (row > 17 && col < 7) return (row + col) % 2 === 0 || row === 18 || col === 0 || row === 24 || col === 6;
    return pseudoRandom > 50;
  },

  // ===== 颜色工具 =====
  generatePalette(count = 5) {
    const colors = [];
    const hue = Math.floor(Math.random() * 360);
    for (let i = 0; i < count; i++) {
      colors.push(this.hslToHex((hue + i * (360 / count)) % 360, 70, 60));
    }
    return colors;
  },

  hslToHex(h, s, l) {
    s /= 100;
    l /= 100;
    const a = s * Math.min(l, 1 - l);
    const f = n => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color).toString(16).padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  },

  // ===== 时间戳转换 =====
  timestampConvert(input) {
    let ts, dt;

    if (/^\d{10,13}$/.test(input)) {
      ts = parseInt(input.length === 13 ? input / 1000 : input);
      dt = new Date(ts * 1000);
    } else {
      dt = new Date(input);
      ts = Math.floor(dt.getTime() / 1000);
    }

    if (isNaN(dt.getTime())) return { error: '无效的时间' };

    return {
      timestamp: ts,
      datetime: dt.toLocaleString('zh-CN'),
      iso: dt.toISOString(),
      relative: this.getRelativeTime(ts),
    };
  },

  getRelativeTime(ts) {
    const diff = Math.floor(Date.now() / 1000) - ts;
    if (diff < 60) return '刚刚';
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`;
    if (diff < 2592000) return `${Math.floor(diff / 86400)} 天前`;
    return `${Math.floor(diff / 2592000)} 个月前`;
  },

  // ===== 随机数生成 =====
  randomNumber(min, max, count = 1) {
    const results = [];
    for (let i = 0; i < count; i++) {
      results.push(Math.floor(Math.random() * (max - min + 1)) + min);
    }
    return results;
  },

  // ===== 条形码生成 =====
  generateBarcode(text) {
    const canvas = document.createElement('canvas');
    canvas.width = 300;
    canvas.height = 80;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 300, 80);
    ctx.fillStyle = '#000000';

    const barWidth = 2;
    let x = 10;
    for (let i = 0; i < text.length; i++) {
      const code = text.charCodeAt(i);
      for (let j = 0; j < 8; j++) {
        if ((code >> j) & 1) {
          ctx.fillRect(x, 10, barWidth, 50);
        }
        x += barWidth;
      }
    }

    ctx.fillStyle = '#000000';
    ctx.font = '14px monospace';
    ctx.fillText(text, 10, 75);

    return canvas.toDataURL();
  },
};