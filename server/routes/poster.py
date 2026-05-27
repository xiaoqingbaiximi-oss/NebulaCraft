"""
海报生成 API - 增强版
支持: 多模板 / 中文渲染 / 渐变背景 / 二维码嵌入 / 多种尺寸
"""
import io
import os
import time
import random
from server.config import OUTPUT_DIR


# 预设模板
TEMPLATES = {
    "event": {"bg_start": "#6c5ce7", "bg_end": "#a78bfa", "title_size": 72, "style": "活动"},
    "promotion": {"bg_start": "#e74c3c", "bg_end": "#f39c12", "title_size": 64, "style": "促销"},
    "corporate": {"bg_start": "#2c3e50", "bg_end": "#3498db", "title_size": 60, "style": "商务"},
    "festival": {"bg_start": "#c0392b", "bg_end": "#e74c3c", "title_size": 68, "style": "节日"},
    "minimal": {"bg_start": "#ffffff", "bg_end": "#f5f5f5", "title_size": 56, "style": "极简"},
}


def handle(body):
    title = body.get("title", "标题")
    subtitle = body.get("subtitle", "副标题")
    template = body.get("template", "event")
    width = min(int(body.get("width", 800)), 1200)
    height = min(int(body.get("height", 1200)), 1600)
    footer = body.get("footer", "NebulaCraft AI")
    qr_content = body.get("qr_content", "")
    
    # 获取模板
    tpl = TEMPLATES.get(template, TEMPLATES["event"])
    
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        
        # 创建渐变背景
        img = _create_gradient_background(
            width, height,
            tpl["bg_start"], tpl["bg_end"]
        )
        draw = ImageDraw.Draw(img)
        
        # 装饰元素
        _add_decorations(draw, width, height)
        
        # 加载字体
        title_font = _load_font(tpl["title_size"])
        subtitle_font = _load_font(36)
        footer_font = _load_font(24)
        
        # 标题
        title_color = "#ffffff" if template != "minimal" else "#2c3e50"
        _draw_centered_text(draw, title, title_font, width // 2, height // 3, title_color)
        
        # 副标题
        if subtitle:
            subtitle_color = "rgba(255,255,255,0.85)" if template != "minimal" else "rgba(44,62,80,0.8)"
            _draw_centered_text(draw, subtitle, subtitle_font, width // 2, height // 3 + 80, subtitle_color)
        
        # 分隔线
        line_y = height // 2 + 20
        draw.line(
            [(width // 4, line_y), (width * 3 // 4, line_y)],
            fill="rgba(255,255,255,0.3)" if template != "minimal" else "rgba(0,0,0,0.2)",
            width=2,
        )
        
        # 底部信息
        footer_color = "rgba(255,255,255,0.6)" if template != "minimal" else "rgba(0,0,0,0.5)"
        draw.text((40, height - 50), footer, fill=footer_color, font=footer_font)
        
        # 日期
        date_str = time.strftime("%Y.%m.%d")
        draw.text((width - 160, height - 50), date_str, fill=footer_color, font=footer_font)
        
        # 二维码
        if qr_content:
            _add_qr_code(img, qr_content, width - 120, height - 120, 100)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG", quality=95)
        
        file_id = f"poster_{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, file_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "size": f"{width}x{height}",
            "template": template,
        }
    
    except Exception as e:
        return {"ok": False, "error": f"海报生成失败: {e}"}


def _create_gradient_background(width, height, color_start, color_end):
    """创建渐变背景"""
    from PIL import Image
    
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    r1, g1, b1 = _hex_to_rgb(color_start)
    r2, g2, b2 = _hex_to_rgb(color_end)
    
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        for x in range(width):
            pixels[x, y] = (r, g, b)
    
    return img


def _add_decorations(draw, width, height):
    """添加装饰元素"""
    from PIL import ImageDraw
    
    # 圆圈装饰
    for i in range(5):
        x = random.randint(width // 4, width * 3 // 4)
        y = random.randint(height // 4, height * 3 // 4)
        r = random.randint(50, 200)
        alpha = random.randint(10, 30)
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            outline=f"rgba(255,255,255,{alpha})",
            width=random.randint(1, 4),
        )
    
    # 点状装饰
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(2, 6)
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill="rgba(255,255,255,40)",
        )


def _draw_centered_text(draw, text, font, x, y, fill):
    """居中绘制文字"""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw // 2, y - th // 2), text, fill=fill, font=font)


def _load_font(size):
    """加载字体（优先中文字体）"""
    from PIL import ImageFont
    
    # 尝试多个中文字体路径
    font_paths = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    
    # 兜底
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()


def _add_qr_code(img, content, x, y, size):
    """添加二维码"""
    try:
        import qrcode
        from PIL import Image
        
        qr = qrcode.QRCode(box_size=3, border=2)
        qr.add_data(content)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        qr_img = qr_img.resize((size, size), Image.LANCZOS)
        
        # 白色背景
        bg = Image.new("RGBA", (size + 20, size + 20), (255, 255, 255, 230))
        bg.paste(qr_img, (10, 10))
        
        img.paste(bg, (x - size // 2 - 10, y - size // 2 - 10), bg)
    except ImportError:
        pass  # 无 qrcode 库则跳过


def _hex_to_rgb(hex_color):
    """HEX 转 RGB"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))