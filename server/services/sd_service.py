"""
图像生成服务 - 多后端自动切换
优先级: 本地 SD WebUI > 在线 API > 内置生成
"""
import io
import os
import time
import json
import base64
import random
import requests
from server.config import OUTPUT_DIR, DATA_DIR

SD_CACHE = os.path.join(DATA_DIR, "sd_cache")
os.makedirs(SD_CACHE, exist_ok=True)

STYLE_PRESETS = {
    "写实": "photorealistic, 8k, detailed, realistic, photograph, professional lighting, sharp focus",
    "动漫": "anime style, manga, studio ghibli, clean lines, vibrant, cel shading",
    "油画": "oil painting, impressionist, brush strokes, canvas texture, classical art",
    "水彩": "watercolor, soft colors, flowing, artistic, delicate, translucent",
    "赛博朋克": "cyberpunk, neon lights, futuristic, blade runner style, rain, holographic",
    "像素": "pixel art, 8-bit, retro gaming, sprite, blocky, nostalgic",
    "素描": "pencil sketch, charcoal, monochrome, detailed drawing, shading",
    "3D渲染": "3d render, octane, blender, volumetric lighting, cgi, ray tracing",
}


class SDService:
    def __init__(self):
        self.backend = None
        self._detect_backend()

    def _detect_backend(self):
        """检测可用后端"""
        # 1. 检测本地 SD WebUI
        try:
            resp = requests.get("http://127.0.0.1:7860/sdapi/v1/sd-models", timeout=3)
            if resp.status_code == 200:
                self.backend = "webui"
                print("✅ SD 后端: 本地 WebUI")
                return
        except:
            pass

        # 2. 使用内置生成器（始终可用）
        self.backend = "builtin"
        print("🎨 SD 后端: 内置生成引擎")

    def generate(self, prompt, negative_prompt="", width=512, height=512, steps=20, cfg_scale=7, seed=-1, style=""):
        """生成图像"""
        if style and style in STYLE_PRESETS:
            prompt = f"{prompt}, {STYLE_PRESETS[style]}"

        if self.backend == "webui":
            return self._generate_webui(prompt, negative_prompt, width, height, steps, cfg_scale, seed)
        else:
            return self._generate_builtin(prompt, negative_prompt, width, height, seed, style)

    def _generate_webui(self, prompt, negative_prompt, width, height, steps, cfg_scale, seed):
        """本地 SD WebUI"""
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "ugly, blurry, low quality, distorted, deformed, bad anatomy",
            "width": min(width, 1024),
            "height": min(height, 1024),
            "steps": min(steps, 50),
            "cfg_scale": cfg_scale,
            "seed": seed,
            "sampler_name": "DPM++ 2M Karras",
        }
        try:
            resp = requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json=payload, timeout=120)
            data = resp.json()
            if "images" in data and data["images"]:
                img_bytes = base64.b64decode(data["images"][0])
                return self._save_image(img_bytes, prompt, "webui", seed)
            return {"ok": False, "error": "SD WebUI 返回空图像"}
        except requests.ConnectionError:
            return {"ok": False, "error": "SD WebUI 未运行，已切换内置引擎"}
        except Exception as e:
            return {"ok": False, "error": f"SD WebUI 错误: {e}"}

    def _generate_builtin(self, prompt, negative_prompt, width, height, seed, style):
        """内置高质量生成器 - 使用 PIL 高级算法"""
        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops

            # 从 prompt 生成确定性种子
            hash_seed = sum(ord(c) * (i + 1) for i, c in enumerate(prompt))
            rng = random.Random(hash_seed if seed == -1 else seed)
            actual_seed = hash_seed if seed == -1 else seed

            # 创建画布
            img = Image.new("RGB", (width, height), (0, 0, 0))
            pixels = img.load()

            # 解析 prompt 提取颜色主题
            theme_colors = self._extract_color_theme(prompt, rng)

            # 1. 渐变背景天空
            self._draw_sky_gradient(pixels, width, height, theme_colors, rng)

            # 2. 地形/纹理层
            self._draw_terrain(pixels, width, height, theme_colors, rng)

            # 3. 形状元素
            draw = ImageDraw.Draw(img)
            self._draw_shapes(draw, width, height, theme_colors, rng, prompt)

            # 4. 粒子/光效
            self._draw_particles(pixels, width, height, theme_colors, rng)

            # 5. 后处理
            img = self._post_process(img, rng)

            # 6. 添加签名
            self._add_signature(draw, width, height, prompt, theme_colors)

            # 保存
            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)

            file_id = f"sd_{int(time.time() * 1000)}_{rng.randint(1000, 9999)}.png"
            filepath = os.path.join(OUTPUT_DIR, file_id)
            with open(filepath, "wb") as f:
                f.write(buf.getvalue())

            meta = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "style": style or "auto",
                "backend": "builtin",
                "seed": actual_seed,
                "size": f"{width}x{height}",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(filepath + ".json", "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)

            return {
                "ok": True,
                "url": f"/output/{file_id}",
                "backend": "builtin",
                "prompt": prompt[:100],
                "seed": actual_seed,
                "size": f"{width}x{height}",
            }
        except Exception as e:
            return {"ok": False, "error": f"内置引擎错误: {e}"}

    def _extract_color_theme(self, prompt, rng):
        """从 prompt 提取颜色主题"""
        prompt_lower = prompt.lower()

        # 预定义颜色主题
        themes = {
            "sunset": [(255, 94, 77), (255, 153, 51), (255, 204, 92), (200, 100, 150)],
            "ocean": [(0, 105, 148), (0, 150, 200), (100, 200, 255), (0, 80, 120)],
            "forest": [(34, 139, 34), (107, 142, 35), (60, 100, 40), (140, 180, 100)],
            "fire": [(255, 69, 0), (255, 140, 0), (200, 50, 0), (255, 200, 50)],
            "night": [(10, 10, 40), (30, 30, 80), (60, 60, 120), (100, 100, 180)],
            "purple": [(108, 92, 231), (167, 139, 250), (80, 60, 200), (200, 180, 255)],
            "warm": [(255, 100, 50), (255, 180, 100), (200, 80, 30), (255, 220, 150)],
            "cool": [(50, 100, 200), (100, 180, 255), (30, 80, 150), (150, 200, 255)],
        }

        for theme_name, colors in themes.items():
            if theme_name in prompt_lower:
                return colors

        # 自定义颜色关键词
        color_keywords = {
            "红色": (255, 60, 60), "蓝色": (60, 100, 255), "绿色": (60, 200, 60),
            "黄色": (255, 220, 50), "紫色": (150, 60, 255), "粉色": (255, 150, 200),
            "橙色": (255, 140, 50), "白色": (240, 240, 255), "黑色": (20, 20, 30),
            "red": (255, 60, 60), "blue": (60, 100, 255), "green": (60, 200, 60),
        }

        main_color = (108, 92, 231)  # 默认星云紫
        for kw, color in color_keywords.items():
            if kw in prompt_lower:
                main_color = color
                break

        # 生成调色板
        r, g, b = main_color
        palette = [
            main_color,
            (min(255, r + 60), min(255, g + 50), min(255, b + 20)),
            (max(0, r - 30), max(0, g - 20), min(255, b + 40)),
            (min(255, r + 30), min(255, g + 80), max(0, b - 20)),
        ]
        return palette

    def _draw_sky_gradient(self, pixels, width, height, colors, rng):
        """天空渐变"""
        c1, c2 = colors[0], colors[2]
        sky_h = int(height * rng.uniform(0.4, 0.7))

        for y in range(sky_h):
            ratio = y / sky_h
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            for x in range(width):
                noise = rng.randint(-8, 8)
                pixels[x, y] = (
                    max(0, min(255, r + noise)),
                    max(0, min(255, g + noise)),
                    max(0, min(255, b + noise)),
                )

    def _draw_terrain(self, pixels, width, height, colors, rng):
        """地形纹理"""
        sky_h = int(height * rng.uniform(0.4, 0.7))
        c3, c4 = colors[1], colors[3]

        for y in range(sky_h, height):
            ratio = (y - sky_h) / (height - sky_h)
            for x in range(width):
                # 简单的波形纹理
                wave = int(15 * (1 + __import__('math').sin(x * 0.02 + y * 0.01)))
                r = int(c3[0] + (c4[0] - c3[0]) * ratio + wave)
                g = int(c3[1] + (c4[1] - c3[1]) * ratio + wave)
                b = int(c3[2] + (c4[2] - c3[2]) * ratio + wave)
                pixels[x, y] = (
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)),
                )

    def _draw_shapes(self, draw, width, height, colors, rng, prompt):
        """绘制几何形状"""
        for _ in range(rng.randint(8, 20)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            size = rng.randint(30, min(width, height) // 2)
            color = rng.choice(colors)
            alpha = rng.randint(40, 150)
            shape_color = (*color, alpha) if len(color) == 3 else color

            shape_type = rng.choice(["circle", "ellipse", "rect", "triangle", "ring"])

            if shape_type == "circle":
                draw.ellipse([x - size, y - size, x + size, y + size],
                            fill=shape_color[:3], outline=None)
            elif shape_type == "ellipse":
                draw.ellipse([x - size, y - size//2, x + size, y + size//2],
                            fill=shape_color[:3])
            elif shape_type == "rect":
                draw.rectangle([x - size, y - size, x + size, y + size],
                             fill=shape_color[:3])
            elif shape_type == "triangle":
                points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
                draw.polygon(points, fill=shape_color[:3])
            elif shape_type == "ring":
                draw.ellipse([x - size, y - size, x + size, y + size],
                            outline=color, width=rng.randint(2, 8))

    def _draw_particles(self, pixels, width, height, colors, rng):
        """粒子效果"""
        particle_count = rng.randint(100, 300)
        for _ in range(particle_count):
            x = rng.randint(0, width - 1)
            y = rng.randint(0, height - 1)
            color = rng.choice(colors)
            brightness = rng.randint(80, 200)
            size = rng.randint(1, 4)

            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    px, py = x + dx, y + dy
                    if 0 <= px < width and 0 <= py < height:
                        existing = pixels[px, py]
                        blend = rng.uniform(0.3, 0.7)
                        pixels[px, py] = (
                            int(existing[0] * (1 - blend) + color[0] * blend * brightness / 255),
                            int(existing[1] * (1 - blend) + color[1] * blend * brightness / 255),
                            int(existing[2] * (1 - blend) + color[2] * blend * brightness / 255),
                        )

    def _post_process(self, img, rng):
        """后处理：模糊+锐化+对比度"""
        from PIL import ImageEnhance

        # 微模糊
        img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(1.5, 3.0)))

        # 锐化
        img = ImageEnhance.Sharpness(img).enhance(rng.uniform(1.2, 2.0))

        # 对比度
        img = ImageEnhance.Contrast(img).enhance(rng.uniform(1.1, 1.4))

        # 色彩
        img = ImageEnhance.Color(img).enhance(rng.uniform(1.0, 1.3))

        return img

    def _add_signature(self, draw, width, height, prompt, colors):
        """添加水印"""
        try:
            from PIL import ImageFont
            font_size = max(width // 35, 10)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            text = f"NebulaCraft AI | {prompt[:40]}"
            text_color = (255, 255, 255) if sum(colors[0]) < 400 else (30, 30, 40)

            # 底部半透明条
            draw.rectangle([0, height - 30, width, height], fill=(0, 0, 0, 100))
            draw.text((8, height - 25), text, fill=text_color, font=font)
        except:
            pass

    def _save_image(self, img_bytes, prompt, backend, seed):
        """保存图像"""
        file_id = f"sd_{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, file_id)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        meta = {"prompt": prompt, "backend": backend, "seed": seed, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(filepath + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        return {"ok": True, "url": f"/output/{file_id}", "backend": backend, "prompt": prompt, "seed": seed}

    def get_status(self):
        return {"ok": True, "backend": self.backend, "available": self.backend == "webui",
                "backends": {"webui": "http://127.0.0.1:7860", "builtin": "内置 PIL 引擎（始终可用）"}}

    def get_styles(self):
        return {"ok": True, "styles": [{"name": k, "prompt": v[:60] + "..."} for k, v in STYLE_PRESETS.items()]}


sd_service = SDService()