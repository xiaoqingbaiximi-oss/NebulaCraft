"""
Stable Diffusion 图像生成服务
支持: SD WebUI / ComfyUI / HuggingFace / 本地兜底
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

# 预设风格
STYLE_PRESETS = {
    "写实": "photorealistic, 8k, detailed, realistic, photograph",
    "动漫": "anime style, manga, studio ghibli, clean lines",
    "油画": "oil painting, impressionist, brush strokes, canvas texture",
    "水彩": "watercolor, soft colors, flowing, artistic",
    "赛博朋克": "cyberpunk, neon lights, futuristic, blade runner style",
    "像素": "pixel art, 8-bit, retro gaming, sprite",
    "素描": "pencil sketch, charcoal, monochrome, detailed drawing",
    "3D渲染": "3d render, octane, blender, volumetric lighting, cgi",
}


class SDService:
    def __init__(self):
        self.backend = None
        self._detect_backend()
    
    def _detect_backend(self):
        """自动检测可用的后端"""
        # 1. 检测本地 SD WebUI
        try:
            resp = requests.get("http://127.0.0.1:7860/sdapi/v1/sd-models", timeout=3)
            if resp.status_code == 200:
                self.backend = "webui"
                print("✅ SD 后端: 本地 WebUI")
                return
        except:
            pass
        
        # 2. 检测 ComfyUI
        try:
            resp = requests.get("http://127.0.0.1:8188/system_stats", timeout=3)
            if resp.status_code == 200:
                self.backend = "comfyui"
                print("✅ SD 后端: ComfyUI")
                return
        except:
            pass
        
        # 3. 检查 HuggingFace Token
        if os.environ.get("HF_TOKEN"):
            self.backend = "huggingface"
            print("✅ SD 后端: HuggingFace")
            return
        
        # 4. 兜底
        self.backend = "fallback"
        print("⚠️ SD 后端: 本地兜底（Pillow）")
    
    def generate(self, prompt, negative_prompt="", width=512, height=512, steps=20, cfg_scale=7, seed=-1, style=""):
        """生成图像"""
        if style and style in STYLE_PRESETS:
            prompt = f"{prompt}, {STYLE_PRESETS[style]}"
        
        if self.backend == "webui":
            return self._generate_webui(prompt, negative_prompt, width, height, steps, cfg_scale, seed)
        elif self.backend == "comfyui":
            return self._generate_comfyui(prompt, negative_prompt, width, height, steps, cfg_scale, seed)
        elif self.backend == "huggingface":
            return self._generate_huggingface(prompt, negative_prompt, width, height)
        else:
            return self._generate_fallback(prompt, width, height)
    
    def _generate_webui(self, prompt, negative_prompt, width, height, steps, cfg_scale, seed):
        """调用 SD WebUI API"""
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "ugly, blurry, low quality, distorted, deformed",
            "width": min(width, 1024),
            "height": min(height, 1024),
            "steps": min(steps, 50),
            "cfg_scale": cfg_scale,
            "seed": seed,
            "sampler_name": "DPM++ 2M Karras",
        }
        
        try:
            resp = requests.post(
                "http://127.0.0.1:7860/sdapi/v1/txt2img",
                json=payload,
                timeout=120,
            )
            data = resp.json()
            
            if "images" in data and data["images"]:
                img_bytes = base64.b64decode(data["images"][0])
                return self._save_image(img_bytes, prompt, "webui", seed)
            
            return {"ok": False, "error": "SD WebUI 返回空图像"}
        except requests.ConnectionError:
            return {"ok": False, "error": "SD WebUI 未运行，请启动后重试"}
        except Exception as e:
            return {"ok": False, "error": f"SD WebUI 错误: {e}"}
    
    def _generate_comfyui(self, prompt, negative_prompt, width, height, steps, cfg_scale, seed):
        """调用 ComfyUI API"""
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": 1}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["4", 1]}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt or "ugly, blurry", "clip": ["4", 1]}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "nebulacraft", "images": ["8", 0]}
            },
        }
        
        try:
            resp = requests.post(
                "http://127.0.0.1:8188/prompt",
                json={"prompt": workflow},
                timeout=120,
            )
            data = resp.json()
            
            if "prompt_id" in data:
                # 等待生成完成
                prompt_id = data["prompt_id"]
                time.sleep(2)
                
                # 获取最新图像
                output_dir = os.path.expanduser("~/ComfyUI/output")
                files = sorted(os.listdir(output_dir), key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
                
                for f in files:
                    if f.startswith("nebulacraft"):
                        with open(os.path.join(output_dir, f), "rb") as img_file:
                            return self._save_image(img_file.read(), prompt, "comfyui", seed)
                
                return {"ok": False, "error": "ComfyUI 图像未找到"}
            
            return {"ok": False, "error": "ComfyUI 返回异常"}
        except requests.ConnectionError:
            return {"ok": False, "error": "ComfyUI 未运行"}
        except Exception as e:
            return {"ok": False, "error": f"ComfyUI 错误: {e}"}
    
    def _generate_huggingface(self, prompt, negative_prompt, width, height):
        """调用 HuggingFace API"""
        token = os.environ.get("HF_TOKEN")
        if not token:
            return {"ok": False, "error": "未设置 HF_TOKEN"}
        
        try:
            resp = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt, "negative_prompt": negative_prompt},
                timeout=60,
            )
            
            if resp.status_code == 200:
                return self._save_image(resp.content, prompt, "huggingface", 0)
            
            return {"ok": False, "error": f"HuggingFace 返回 {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "error": f"HuggingFace 错误: {e}"}
    
    def _generate_fallback(self, prompt, width, height):
        """兜底方案：增强版 Pillow 几何艺术"""
        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageFont
            
            img = Image.new("RGB", (width, height), (20, 20, 40))
            draw = ImageDraw.Draw(img)
            
            # 从 prompt 生成种子
            seed = sum(ord(c) for c in prompt)
            rng = random.Random(seed)
            
            # 提取颜色关键词
            colors = [
                (108, 92, 231), (167, 139, 250), (16, 185, 129),
                (245, 158, 11), (239, 68, 68), (59, 130, 246),
                (236, 72, 153), (139, 92, 246), (255, 193, 7),
            ]
            
            # 多层绘制
            for layer in range(3):
                layer_alpha = 0.3 + layer * 0.2
                for _ in range(15):
                    x = rng.randint(0, width)
                    y = rng.randint(0, height)
                    r = rng.randint(20, min(width, height) // 3)
                    color = rng.choice(colors)
                    
                    shape = rng.choice(["circle", "rect", "triangle"])
                    if shape == "circle":
                        draw.ellipse([x - r, y - r, x + r, y + r],
                                     fill=tuple(int(c * layer_alpha) for c in color))
                    elif shape == "rect":
                        draw.rectangle([x - r, y - r, x + r, y + r],
                                      fill=tuple(int(c * layer_alpha) for c in color))
                    else:
                        points = [(x, y - r), (x - r, y + r), (x + r, y + r)]
                        draw.polygon(points, fill=tuple(int(c * layer_alpha) for c in color))
            
            # 模糊 + 锐化
            img = img.filter(ImageFilter.GaussianBlur(radius=3))
            from PIL import ImageEnhance
            img = ImageEnhance.Sharpness(img).enhance(1.5)
            img = ImageEnhance.Contrast(img).enhance(1.3)
            
            # 底部标签
            try:
                font = ImageFont.truetype("arial.ttf", max(width // 30, 12))
            except:
                font = ImageFont.load_default()
            draw.text((10, height - 25), f"NebulaCraft AI | {prompt[:50]}",
                     fill=(200, 200, 220), font=font)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            file_id = f"sd_{int(time.time() * 1000)}_{rng.randint(1000, 9999)}.png"
            filepath = os.path.join(OUTPUT_DIR, file_id)
            with open(filepath, "wb") as f:
                f.write(buf.getvalue())
            
            return {
                "ok": True,
                "url": f"/output/{file_id}",
                "backend": "fallback",
                "prompt": prompt,
                "size": f"{width}x{height}",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _save_image(self, img_bytes, prompt, backend, seed):
        """保存图像文件"""
        file_id = f"sd_{int(time.time() * 1000)}.png"
        filepath = os.path.join(OUTPUT_DIR, file_id)
        
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        
        # 保存 prompt 记录
        meta = {
            "prompt": prompt,
            "backend": backend,
            "seed": seed,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(filepath + ".json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "backend": backend,
            "prompt": prompt,
            "seed": seed,
        }
    
    def get_status(self):
        """获取后端状态"""
        return {
            "ok": True,
            "backend": self.backend,
            "available": self.backend != "fallback",
            "backends": {
                "webui": "http://127.0.0.1:7860",
                "comfyui": "http://127.0.0.1:8188",
                "huggingface": "需要 HF_TOKEN",
                "fallback": "本地 Pillow（始终可用）",
            }
        }
    
    def get_styles(self):
        """获取预设风格列表"""
        return {"ok": True, "styles": [{"name": k, "prompt": v[:80] + "..."} for k, v in STYLE_PRESETS.items()]}


sd_service = SDService()