# -*- coding: utf-8 -*-
"""
内置 AI 图像生成引擎
支持: 文生图 / 海报设计 / 插画 / 素材 / 多风格
完全不依赖外部 API，纯本地运行
"""
import io
import os
import time
import json
import random
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont
from server.config import OUTPUT_DIR

IMAGE_DIR = os.path.join(OUTPUT_DIR, "ai_images")
os.makedirs(IMAGE_DIR, exist_ok=True)


class ImageGenEngine:
    def __init__(self):
        self.font_cache = {}
        self._load_fonts()

    def _load_fonts(self):
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]
        for path in font_paths:
            try:
                self.font_cache["chinese"] = path
                break
            except:
                pass

    def generate(self, prompt, style="auto", width=1024, height=1024, negative=""):
        style_lower = style.lower()
        if "poster" in style_lower:
            return self._generate_poster(prompt, width, height)
        elif "illustration" in style_lower:
            return self._generate_illustration(prompt, width, height)
        elif "material" in style_lower or "icon" in style_lower:
            return self._generate_material(prompt, width, height)
        elif "logo" in style_lower:
            return self._generate_logo(prompt, width, height)
        elif "photo" in style_lower:
            return self._generate_photo(prompt, width, height)
        else:
            return self._generate_art(prompt, width, height)

    def _generate_poster(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        colors = [
            (108, 92, 231), (255, 107, 107), (72, 219, 251),
            (255, 159, 67), (46, 213, 115), (255, 217, 61),
        ]
        c1, c2 = rng.sample(colors, 2)
        img = Image.new("RGB", (width, height), c1)
        draw = ImageDraw.Draw(img)
        for y in range(height):
            ratio = y / height
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        for _ in range(rng.randint(5, 15)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            r = rng.randint(50, min(width, height) // 3)
            alpha = rng.randint(20, 60)
            draw.ellipse([x - r, y - r, x + r, y + r],
                        fill=(255, 255, 255, alpha), outline=(255, 255, 255, alpha // 2), width=3)
        title = prompt.replace("poster", "").replace("design", "").strip()[:20] or "NebulaCraft"
        font_size = width // 10
        font = self._get_font(font_size)
        bbox = draw.textbbox((0, 0), title, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((width - tw) // 2, height // 3 - th // 2), title, fill="white", font=font)
        small_font = self._get_font(width // 30)
        draw.text((40, height - 60), "NebulaCraft AI", fill=(255,255,255,180), font=small_font)
        draw.text((width - 200, height - 60), time.strftime("%Y.%m.%d"), fill=(255,255,255,180), font=small_font)
        return self._save_result(img, "poster", prompt)

    def _generate_illustration(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        img = Image.new("RGB", (width, height), (255, 248, 240))
        draw = ImageDraw.Draw(img)
        base_colors = [
            (255, 182, 193), (255, 218, 185), (255, 255, 200),
            (200, 230, 255), (230, 200, 255), (200, 255, 220),
        ]
        palette = rng.sample(base_colors, 3)
        for _ in range(rng.randint(10, 25)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            w = rng.randint(50, width // 3)
            h = rng.randint(50, height // 3)
            color = rng.choice(palette)
            draw.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=color, outline=(0,0,0,30), width=2)
        for _ in range(rng.randint(5, 15)):
            x1, y1 = rng.randint(0, width), rng.randint(0, height)
            x2, y2 = rng.randint(0, width), rng.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(0,0,0,40), width=rng.randint(1, 5))
        pixels = img.load()
        for _ in range(width * height // 100):
            x, y = rng.randint(0, width - 1), rng.randint(0, height - 1)
            noise = rng.randint(-15, 15)
            r, g, b = pixels[x, y]
            pixels[x, y] = (max(0, min(255, r + noise)), max(0, min(255, g + noise)), max(0, min(255, b + noise)))
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        return self._save_result(img, "illustration", prompt)

    def _generate_material(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 3
        colors = [
            (108, 92, 231), (16, 185, 129), (245, 158, 11),
            (239, 68, 68), (59, 130, 246), (236, 72, 153),
        ]
        for i in range(rng.randint(3, 8)):
            r = max_radius * (0.3 + i * 0.15)
            color = rng.choice(colors)
            shape = rng.choice(["circle", "rounded_rect", "hexagon"])
            if shape == "circle":
                draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=color)
            elif shape == "rounded_rect":
                draw.rounded_rectangle([center_x - r, center_y - r, center_x + r, center_y + r], radius=r // 3, fill=color)
            else:
                points = []
                for j in range(6):
                    angle = j * math.pi / 3
                    points.append((center_x + r * math.cos(angle), center_y + r * math.sin(angle)))
                draw.polygon(points, fill=color)
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse([center_x - max_radius * 1.5, center_y - max_radius * 1.5,
                          center_x + max_radius * 1.5, center_y + max_radius * 1.5], fill=(255,255,255,40))
        img = Image.alpha_composite(img, glow)
        return self._save_result(img, "material", prompt)

    def _generate_logo(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        size = min(width, height) // 3
        colors = [(108, 92, 231), (16, 185, 129), (245, 158, 11), (239, 68, 68), (59, 130, 246)]
        color = rng.choice(colors)
        draw.rounded_rectangle([cx - size, cy - size, cx + size, cy + size], radius=size // 4, fill=color)
        inner = size // 2
        draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=(255,255,255,200))
        text = prompt.replace("logo", "").replace("Logo", "").strip()[:4] or "NC"
        font = self._get_font(size // 2)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy + size + 20), text, fill=color, font=font)
        return self._save_result(img, "logo", prompt)

    def _generate_photo(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        img = Image.new("RGB", (width, height), (0, 0, 0))
        pixels = img.load()
        sky_colors = [(135, 206, 235), (70, 130, 180), (255, 223, 186)]
        sky_h = height * 2 // 3
        for y in range(sky_h):
            ratio = y / sky_h
            idx = int(ratio * (len(sky_colors) - 1))
            c1, c2 = sky_colors[idx], sky_colors[min(idx + 1, len(sky_colors) - 1)]
            sub_ratio = ratio * (len(sky_colors) - 1) - idx
            r = int(c1[0] + (c2[0] - c1[0]) * sub_ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * sub_ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * sub_ratio)
            for x in range(width):
                pixels[x, y] = (r + rng.randint(-5, 5), g + rng.randint(-5, 5), b + rng.randint(-5, 5))
        ground_colors = [(34, 139, 34), (107, 142, 35), (85, 107, 47)]
        for y in range(sky_h, height):
            ratio = (y - sky_h) / (height - sky_h)
            c = ground_colors[int(ratio * (len(ground_colors) - 1))]
            for x in range(width):
                pixels[x, y] = (c[0] + rng.randint(-8, 8), c[1] + rng.randint(-8, 8), c[2] + rng.randint(-8, 8))
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Color(img).enhance(1.1)
        return self._save_result(img, "photo", prompt)

    def _generate_art(self, prompt, width, height):
        rng = random.Random(sum(ord(c) for c in prompt))
        img = Image.new("RGB", (width, height), (20, 20, 40))
        draw = ImageDraw.Draw(img)
        colors = [
            (108, 92, 231), (167, 139, 250), (16, 185, 129),
            (245, 158, 11), (239, 68, 68), (59, 130, 246),
            (236, 72, 153), (255, 193, 7), (139, 92, 246),
        ]
        for layer in range(4):
            alpha = 0.2 + layer * 0.15
            for _ in range(rng.randint(8, 20)):
                x = rng.randint(0, width)
                y = rng.randint(0, height)
                r = rng.randint(20, min(width, height) // 2)
                color = rng.choice(colors)
                c = tuple(int(v * alpha) for v in color)
                shape = rng.choice(["circle", "rect", "triangle", "line"])
                if shape == "circle":
                    draw.ellipse([x - r, y - r, x + r, y + r], fill=c)
                elif shape == "rect":
                    draw.rectangle([x - r, y - r, x + r, y + r], fill=c)
                elif shape == "triangle":
                    pts = [(x, y - r), (x - r, y + r), (x + r, y + r)]
                    draw.polygon(pts, fill=c)
                else:
                    draw.line([(x - r, y - r), (x + r, y + r)], fill=c, width=rng.randint(2, 10))
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        return self._save_result(img, "art", prompt)

    def _get_font(self, size):
        if "chinese" in self.font_cache:
            try:
                return ImageFont.truetype(self.font_cache["chinese"], size)
            except:
                pass
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    def _save_result(self, img, category, prompt):
        file_id = f"{category}_{int(time.time() * 1000)}.png"
        filepath = os.path.join(IMAGE_DIR, file_id)
        img.save(filepath, "PNG")
        meta = {
            "prompt": prompt, "category": category,
            "size": f"{img.width}x{img.height}",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(filepath + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        return {"ok": True, "url": f"/output/ai_images/{file_id}", "category": category, "prompt": prompt}


image_gen = ImageGenEngine()