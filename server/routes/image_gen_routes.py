# -*- coding: utf-8 -*-
"""图片生成 API"""
from server.services.cloud_image import generate_image, get_available_styles, get_platforms


def handle(body):
    prompt = body.get("prompt", "").strip()
    style = body.get("style", "auto")
    width = int(body.get("width", 1024))
    height = int(body.get("height", 1024))
    platform = body.get("platform", None)

    if not prompt:
        return {"ok": False, "error": "请输入图片描述"}

    return generate_image(prompt, width=width, height=height, style=style, platform=platform)


def handle_styles(body):
    return get_available_styles()


def handle_platforms(body):
    return get_platforms()