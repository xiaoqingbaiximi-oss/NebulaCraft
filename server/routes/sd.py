"""Stable Diffusion API 路由"""
from server.services.sd_service import sd_service


def handle(body):
    """生成图像"""
    prompt = body.get("prompt", "").strip()
    negative = body.get("negative_prompt", "")
    width = min(int(body.get("width", 512)), 1024)
    height = min(int(body.get("height", 512)), 1024)
    steps = min(int(body.get("steps", 20)), 50)
    cfg_scale = float(body.get("cfg_scale", 7))
    seed = int(body.get("seed", -1))
    style = body.get("style", "")
    
    if not prompt:
        return {"ok": False, "error": "请输入图像描述"}
    
    return sd_service.generate(prompt, negative, width, height, steps, cfg_scale, seed, style)


def handle_status(body):
    """获取 SD 状态"""
    return sd_service.get_status()


def handle_styles(body):
    """获取风格列表"""
    return sd_service.get_styles()