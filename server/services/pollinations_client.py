# server/services/pollinations_client.py
"""
Pollinations.ai 生图客户端
完全免费，无需 Key，无需注册
"""
import time
import os
import requests
from PIL import Image
from io import BytesIO
from server.config import OUTPUT_DIR

IMAGE_DIR = os.path.join(OUTPUT_DIR, "ai_images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Pollinations 风格映射
STYLE_MAP = {
    "写实": "photorealistic",
    "动漫": "anime",
    "油画": "oil-painting",
    "水彩": "watercolor",
    "赛博朋克": "cyberpunk",
    "像素": "pixel-art",
    "素描": "pencil-sketch",
    "3D渲染": "3d-render",
    "海报": "poster",
    "Logo": "logo",
}


def generate_pollinations(prompt, style="auto", width=1024, height=1024):
    """
    调用 Pollinations.ai 生成图像
    文档: https://pollinations.ai
    """
    # 拼接风格提示词
    style_prompt = STYLE_MAP.get(style, "")
    full_prompt = f"{prompt}, {style_prompt}" if style_prompt else prompt
    
    # Pollinations API URL 格式
    # https://image.pollinations.ai/prompt/{prompt}?width=xxx&height=xxx&seed=xxx
    encoded_prompt = requests.utils.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img = img.convert("RGB")  # 确保模式一致
            
            file_id = f"pollinations_{int(time.time() * 1000)}.png"
            filepath = os.path.join(IMAGE_DIR, file_id)
            img.save(filepath, "PNG")
            
            return {
                "ok": True,
                "url": f"/output/ai_images/{file_id}",
                "engine": "Pollinations.ai",
                "prompt": prompt,
                "size": f"{img.width}x{img.height}"
            }
        else:
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# 测试
if __name__ == "__main__":
    result = generate_pollinations("一只可爱的柴犬", style="写实")
    print(result)