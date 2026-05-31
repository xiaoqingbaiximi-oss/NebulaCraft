# -*- coding: utf-8 -*-
"""
AI 生图服务 - 全平台集成
支持: 云端API / 本地模型 / 免费代理 / Pillow回退
"""
import os
import random
import base64
import json
import ssl
import urllib.request
import urllib.parse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "output", "ai_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)
API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "api_config.json")

STYLES = ["写实", "动漫", "油画", "水彩", "赛博朋克", "像素", "素描", "3D渲染"]


def _load_config():
    try:
        if os.path.exists(API_CONFIG_FILE):
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}


def _save_bytes(data, prompt):
    file_id = f"ai_{random.randint(100000,999999)}.png"
    filepath = os.path.join(OUTPUT_DIR, file_id)
    with open(filepath, "wb") as f:
        f.write(data)
    return {"ok": True, "url": f"/output/ai_images/{file_id}", "category": "ai", "prompt": prompt}


def _save_pil(img, prompt, style="art"):
    file_id = f"ai_{random.randint(100000,999999)}.png"
    filepath = os.path.join(OUTPUT_DIR, file_id)
    img.save(filepath, "PNG")
    return {"ok": True, "url": f"/output/ai_images/{file_id}", "category": style, "prompt": prompt}


def _ssl_urlopen(url, timeout=15):
    """带浏览器 User-Agent 的 HTTPS 请求"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


# ===== 云端 API =====

def _try_qwen(prompt, width, height, config):
    """通义万相"""
    key = config.get("dashscope_api_key") or config.get("qwen_api_key", "")
    if not key:
        return None
    try:
        import dashscope
        dashscope.api_key = key
        from dashscope import ImageSynthesis
        result = ImageSynthesis.call(model="wan2.1-t2i-turbo", prompt=prompt, n=1, size=f"{width}*{height}")
        if result.status_code == 200 and result.output:
            for img in result.output.results:
                if img.url:
                    resp = urllib.request.urlopen(img.url, timeout=30)
                    return _save_bytes(resp.read(), prompt)
    except:
        pass
    return None


def _try_openai(prompt, width, height, config):
    """OpenAI DALL-E"""
    key = config.get("openai_api_key", "")
    if not key:
        return None
    try:
        size = "1024x1024"
        data = json.dumps({"model": "dall-e-3", "prompt": prompt, "n": 1, "size": size}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=data,
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        resp = json.loads(_ssl_urlopen(req, timeout=60).read())
        if "data" in resp:
            img_url = resp["data"][0]["url"]
            img_data = _ssl_urlopen(img_url, timeout=30).read()
            return _save_bytes(img_data, prompt)
    except:
        pass
    return None


def _try_gemini(prompt, width, height, config):
    """Google Gemini"""
    key = config.get("google_api_key", "")
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
        response = model.generate_content(prompt)
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data'):
                    return _save_bytes(part.inline_data.data, prompt)
    except:
        pass
    return None


def _try_deepseek(prompt, width, height, config):
    """DeepSeek 不支持生图，跳过"""
    return None


# ===== 本地模型 =====

def _check_sd_webui():
    try:
        resp = _ssl_urlopen("http://127.0.0.1:7860/docs", timeout=1)
        return resp.getcode() == 200
    except:
        return False


def _try_sd_webui(prompt, width, height, config):
    """本地 SD WebUI / ComfyUI"""
    if not _check_sd_webui():
        return None
    try:
        data = json.dumps({
            "prompt": prompt + ", masterpiece, best quality",
            "negative_prompt": "lowres, bad anatomy, text, watermark",
            "width": min(width, 768), "height": min(height, 768),
            "steps": 20, "cfg_scale": 7,
        }).encode()
        req = urllib.request.Request("http://127.0.0.1:7860/sdapi/v1/txt2img", data=data,
                        headers={"Content-Type": "application/json"})
        resp = json.loads(_ssl_urlopen(req, timeout=120).read())
        if "images" in resp:
            img_data = base64.b64decode(resp["images"][0])
            return _save_bytes(img_data, prompt)
    except:
        pass
    return None


def _try_diffusers(prompt, width, height, config):
    """本地 Diffusers 库"""
    try:
        from diffusers import StableDiffusionPipeline
        import torch
        pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipe = pipe.to(device)
        image = pipe(prompt, width=min(width,768), height=min(height,768)).images[0]
        return _save_pil(image, prompt, "diffusers")
    except:
        pass
    return None


# ===== 免费代理 =====

def _try_pollinations(prompt, width, height, config):
    """Pollinations.ai - 免费 AI 生图（修复 403）"""
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"
        resp = _ssl_urlopen(url, timeout=60)
        data = resp.read()
        if resp.getcode() == 200 and len(data) > 1000:
            return _save_bytes(data, prompt)
    except Exception as e:
        print(f"[Pollinations] 错误: {e}")
    return None


# ===== Pillow 回退 =====

def _generate_pillow(prompt, width, height, style):
    rng = random.Random(sum(ord(c) for c in prompt))
    img = Image.new("RGB", (width, height), (20, 20, 40))
    draw = ImageDraw.Draw(img)
    
    palettes = {
        "写实": [(135,206,235),(70,130,180),(34,139,34),(107,142,35)],
        "动漫": [(255,182,193),(255,218,185),(200,230,255),(230,200,255)],
        "油画": [(139,69,19),(160,82,45),(184,134,11),(218,165,32)],
        "水彩": [(176,224,230),(255,228,225),(230,230,250),(240,255,240)],
        "赛博朋克": [(255,0,128),(0,255,255),(128,0,255)],
        "像素": [(255,0,0),(0,255,0),(0,0,255),(255,255,0)],
        "素描": [(50,50,50),(100,100,100),(150,150,150),(200,200,200)],
        "3D渲染": [(108,92,231),(167,139,250),(16,185,129),(245,158,11)],
    }
    colors = palettes.get(style, palettes["写实"])
    c1, c2 = rng.sample(colors, 2) if len(colors) >= 2 else (colors[0], colors[-1])
    
    for y in range(height):
        ratio = y / height
        r, g, b = int(c1[0]+(c2[0]-c1[0])*ratio), int(c1[1]+(c2[1]-c1[1])*ratio), int(c1[2]+(c2[2]-c1[2])*ratio)
        draw.line([(0,y),(width,y)], fill=(r,g,b))
    
    for _ in range(rng.randint(5, 20)):
        x, y, r = rng.randint(0,width), rng.randint(0,height), rng.randint(30, min(width,height)//3)
        color, alpha = rng.choice(colors), rng.randint(20, 80)
        c = tuple(int(v*alpha/100) for v in color)
        shape = rng.choice(["circle","rect","triangle"])
        if shape == "circle": draw.ellipse([x-r,y-r,x+r,y+r], fill=c)
        elif shape == "rect": draw.rounded_rectangle([x-r,y-r,x+r,y+r], radius=r//3, fill=c)
        else: draw.polygon([(x,y-r),(x-r,y+r),(x+r,y+r)], fill=c)
    
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Color(img).enhance(1.1)
    return _save_pil(img, prompt, style or "art")


# ===== 主入口 =====

def generate_image(prompt, width=512, height=512, style=None, platform=None):
    config = _load_config()
    
    # 按指定平台或优先级尝试
    platforms = [platform] if platform else [
        "qwen", "openai", "gemini", "sd_webui", "diffusers", "pollinations", "pillow"
    ]
    
    for plat in platforms:
        result = None
        print(f"[ImageGen] 尝试 {plat}...")
        
        if plat == "qwen":
            result = _try_qwen(prompt, width, height, config)
        elif plat == "openai":
            result = _try_openai(prompt, width, height, config)
        elif plat == "gemini":
            result = _try_gemini(prompt, width, height, config)
        elif plat == "sd_webui":
            result = _try_sd_webui(prompt, width, height, config)
        elif plat == "diffusers":
            result = _try_diffusers(prompt, width, height, config)
        elif plat == "pollinations":
            result = _try_pollinations(prompt, width, height, config)
        elif plat == "pillow":
            result = _generate_pillow(prompt, width, height, style)
        
        if result and result.get("ok"):
            print(f"[ImageGen] ✅ {plat} 成功")
            result["engine"] = plat
            return result
        else:
            print(f"[ImageGen] ❌ {plat} 失败")
    
    return _generate_pillow(prompt, width, height, style)


def get_available_styles():
    return {"ok": True, "styles": STYLES}


def get_platforms():
    config = _load_config()
    platforms = []
    if config.get("dashscope_api_key") or config.get("qwen_api_key"):
        platforms.append({"id": "qwen", "name": "通义万相"})
    if config.get("openai_api_key"):
        platforms.append({"id": "openai", "name": "OpenAI DALL-E"})
    if config.get("google_api_key"):
        platforms.append({"id": "gemini", "name": "Google Gemini"})
    if _check_sd_webui():
        platforms.append({"id": "sd_webui", "name": "SD WebUI/ComfyUI"})
    platforms.append({"id": "pollinations", "name": "Pollinations.ai (免费)"})
    platforms.append({"id": "pillow", "name": "内置几何引擎"})
    return {"ok": True, "platforms": platforms}