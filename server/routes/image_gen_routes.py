# -*- coding: utf-8 -*-
"""图片生成 API"""
import re
from server.services.cloud_image import generate_image, get_available_styles, get_platforms


def _clean_prompt(prompt):
    """去掉 @图片 @生成 等指令前缀，只保留描述文字"""
    # 去掉常见的指令前缀
    prompt = re.sub(r'^[@#]?(图片|生成|画|draw|image|generate)\s+', '', prompt, flags=re.IGNORECASE)
    return prompt.strip()


def handle(body):
    prompt = body.get("prompt", "").strip()
    style = body.get("style", "auto")
    width = int(body.get("width", 1024))
    height = int(body.get("height", 1024))
    platform = body.get("platform", None)

    # 清理提示词：去掉 @图片 等前缀
    prompt = _clean_prompt(prompt)

    if not prompt:
        return {"ok": False, "error": "请输入图片描述"}

    return generate_image(prompt, width=width, height=height, style=style, platform=platform)


def handle_styles(body):
    return get_available_styles()


def handle_platforms(body):
    return get_platforms()