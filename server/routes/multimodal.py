"""
多模态视觉分析路由
接收截图 base64 + prompt，调用视觉模型分析
"""
import json
from server.services.ollama import chat, chat_stream, is_available
from server.config import DEFAULT_MODEL


def handle(body: dict) -> dict:
    """
    POST /api/multimodal
    body: {
        "image_base64": "...",
        "prompt": "描述这张图片",
        "model": "llava"  (可选)
    }
    """
    image_base64 = body.get("image_base64", "")
    prompt = body.get("prompt", "Describe this image in detail")
    model = body.get("model", "llava")  # 默认用 llava，也支持 qwen2.5-vl, llava-llama3 等

    if not image_base64:
        return {"ok": False, "error": "No image provided"}

    if not is_available():
        return {"ok": False, "error": "Ollama service not connected"}

    # 调用 Ollama 视觉模型
    messages = [{
        "role": "user",
        "content": prompt,
        "images": [image_base64]
    }]

    try:
        reply = chat(messages, model=model, timeout=120)
        return {"ok": True, "reply": reply}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_stream(body: dict):
    """
    流式版本（可选）
    """
    image_base64 = body.get("image_base64", "")
    prompt = body.get("prompt", "Describe this image")
    model = body.get("model", "llava")

    if not image_base64:
        return lambda: iter(["data: " + json.dumps({"error": "No image provided"}) + "\n\n"])

    messages = [{
        "role": "user",
        "content": prompt,
        "images": [image_base64]
    }]

    def gen():
        try:
            for chunk in chat_stream(messages, model):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return gen