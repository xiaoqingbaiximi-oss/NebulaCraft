"""
设置 API 路由 - 多平台支持
"""
from server.services.cloud_llm import set_api_key, set_custom_api, get_all_status


def handle(body: dict) -> dict:
    action = body.get("action", "status")

    if action == "status":
        return {"ok": True, **get_all_status()}
    if action == "set_api_key":
        platform = body.get("platform", "qwen")
        key = body.get("api_key", "").strip()
        if not key:
            return {"ok": False, "error": "API Key 不能为空"}
        set_api_key(platform, key)
        return {"ok": True, "message": f"{platform} API Key 已保存"}
    if action == "set_custom":
        set_custom_api(
            url=body.get("url", ""),
            key=body.get("api_key", ""),
            models=body.get("models", ""),
            default_model=body.get("default_model", ""),
        )
        return {"ok": True, "message": "自定义 API 已保存"}

    return {"ok": False, "error": "Unknown action"}