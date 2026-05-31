# -*- coding: utf-8 -*-
"""
屏幕截图分析引擎
截取屏幕 → AI 视觉模型分析
"""
import os
import json
import base64
import time as _time
from io import BytesIO
from datetime import datetime
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"  # 文本模型
VISION_MODEL = "llava:latest"  # 视觉模型（需要先 ollama pull llava）

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def capture_screen():
    """截取屏幕"""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        filepath = os.path.join(OUTPUT_DIR, f"screen_{int(_time.time())}.png")
        img.save(filepath, "PNG")
        
        # 转 base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "ok": True,
            "path": filepath,
            "size": f"{img.width}x{img.height}",
            "image_base64": img_base64
        }
    except ImportError:
        return {"ok": False, "error": "PIL 未安装，请运行: pip install pillow"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def analyze_screen(question="屏幕上有什么？"):
    """截图并分析"""
    capture_result = capture_screen()
    if not capture_result.get("ok"):
        return capture_result
    
    try:
        resp = requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": VISION_MODEL,
            "prompt": f"请详细分析这张截图。{question}",
            "images": [capture_result["image_base64"]],
            "stream": False,
            "options": {"num_predict": 500, "temperature": 0.3}
        }, timeout=60)
        
        if resp.status_code == 200:
            analysis = resp.json().get("response", "")
            return {
                "ok": True,
                "path": capture_result["path"],
                "size": capture_result["size"],
                "analysis": analysis,
                "question": question
            }
    except Exception as e:
        # 视觉模型不可用，回退到基础信息
        return {
            "ok": True,
            "path": capture_result["path"],
            "size": capture_result["size"],
            "analysis": f"截图已保存: {capture_result['path']} (视觉模型未安装，无法分析内容)",
            "question": question,
            "note": "安装视觉模型以获得更好体验: ollama pull llava"
        }
    
    return {"ok": False, "error": "分析失败"}


def ai_screen_operation(user_message):
    """AI 处理屏幕相关操作"""
    msg = user_message.lower()
    
    if any(w in msg for w in ["截图", "截屏", "屏幕截图", "screenshot"]):
        if any(w in msg for w in ["分析", "看看", "是什么", "有什么"]):
            question = user_message
            return analyze_screen(question)
        else:
            result = capture_screen()
            if result.get("ok"):
                return {
                    "ok": True,
                    "reply": f"截图已保存: {result['path']} ({result['size']})",
                    "path": result["path"]
                }
            return result
    
    return {"ok": False, "error": "不涉及屏幕操作"}