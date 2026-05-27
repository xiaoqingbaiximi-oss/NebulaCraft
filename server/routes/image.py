"""
图像处理 API - 增强版
支持: AI 图像生成 / 背景移除 / OCR / 图像分析 / 缩略图 / 水印
"""
import io
import os
import time
import random
import base64
from server.config import OUTPUT_DIR


def handle_generate(body):
    """AI 图像生成"""
    prompt = body.get("prompt", "abstract art")
    width = min(int(body.get("width", 512)), 1024)
    height = min(int(body.get("height", 512)), 1024)
    style = body.get("style", "abstract")
    
    try:
        from PIL import Image, ImageDraw, ImageFilter
        
        img = Image.new("RGB", (width, height), (20, 20, 40))
        draw = ImageDraw.Draw(img)
        
        # 根据风格选择颜色方案
        style_palettes = {
            "abstract": [(108, 92, 231), (167, 139, 250), (16, 185, 129), (245, 158, 11), (239, 68, 68)],
            "nature": [(34, 139, 34), (107, 142, 35), (154, 205, 50), (143, 188, 143), (46, 139, 87)],
            "ocean": [(0, 105, 148), (0, 119, 182), (3, 169, 244), (79, 195, 247), (144, 224, 239)],
            "sunset": [(255, 94, 77), (255, 153, 51), (255, 204, 92), (233, 145, 116), (248, 131, 121)],
            "monochrome": [(40, 40, 40), (80, 80, 80), (120, 120, 120), (160, 160, 160), (200, 200, 200)],
        }
        
        colors = style_palettes.get(style, style_palettes["abstract"])
        
        # 随机几何图形
        for _ in range(20):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(20, min(width, height) // 3)
            shape = random.choice(["circle", "rectangle", "triangle"])
            
            color = random.choice(colors)
            
            if shape == "circle":
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            elif shape == "rectangle":
                draw.rectangle([x - r, y - r, x + r, y + r], fill=color)
            else:
                points = [
                    (x, y - r),
                    (x - r, y + r),
                    (x + r, y + r),
                ]
                draw.polygon(points, fill=color)
        
        # 高斯模糊
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        # 添加噪点
        pixels = img.load()
        for i in range(width * height // 20):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            noise = random.randint(-30, 30)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )
        
        # 水印
        draw.text((width - 130, height - 30), "NebulaCraft AI", fill=(180, 180, 200))
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        
        img_id = f"ai_{int(time.time() * 1000)}_{random.randint(1000, 9999)}.png"
        filepath = os.path.join(OUTPUT_DIR, img_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{img_id}",
            "source": "local",
            "style": style,
            "size": f"{width}x{height}",
        }
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_remove_bg(file_data, filename):
    """移除背景"""
    try:
        from PIL import Image
        
        img = Image.open(io.BytesIO(file_data)).convert("RGBA")
        
        # 尝试使用 rembg
        try:
            from rembg import remove
            output = remove(img)
        except ImportError:
            # 简单兜底：白色背景变透明
            datas = img.getdata()
            new_data = []
            for item in datas:
                # 白色/接近白色变透明
                if item[0] > 200 and item[1] > 200 and item[2] > 200:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            output = Image.new("RGBA", img.size)
            output.putdata(new_data)
        
        buf = io.BytesIO()
        output.save(buf, format="PNG")
        
        img_id = f"nobg_{int(time.time() * 1000)}"
        filepath = os.path.join(OUTPUT_DIR, f"{img_id}.png")
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {"ok": True, "url": f"/output/{img_id}.png"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_ocr(file_data):
    """OCR 文字识别"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_data))
        
        try:
            import pytesseract
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            return {"ok": True, "text": text.strip(), "method": "tesseract"}
        except ImportError:
            return {"ok": False, "error": "需要安装 pytesseract 和 Tesseract-OCR"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_thumbnail(file_data, max_size=256):
    """生成缩略图"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_data))
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        
        img_id = f"thumb_{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, img_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {"ok": True, "url": f"/output/{img_id}", "size": f"{img.width}x{img.height}"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_watermark(file_data, text="NebulaCraft", position="bottom-right"):
    """添加水印"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.open(io.BytesIO(file_data)).convert("RGBA")
        
        # 水印层
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 字体
        try:
            font = ImageFont.truetype("arial.ttf", max(img.width // 30, 12))
        except:
            font = ImageFont.load_default()
        
        # 位置
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        padding = 10
        
        positions = {
            "bottom-right": (img.width - tw - padding, img.height - th - padding),
            "bottom-left": (padding, img.height - th - padding),
            "top-right": (img.width - tw - padding, padding),
            "top-left": (padding, padding),
            "center": ((img.width - tw) // 2, (img.height - th) // 2),
        }
        
        pos = positions.get(position, positions["bottom-right"])
        draw.text(pos, text, fill=(255, 255, 255, 80), font=font)
        
        result = Image.alpha_composite(img, overlay)
        
        buf = io.BytesIO()
        result.save(buf, format="PNG")
        
        img_id = f"watermarked_{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, img_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {"ok": True, "url": f"/output/{img_id}"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}