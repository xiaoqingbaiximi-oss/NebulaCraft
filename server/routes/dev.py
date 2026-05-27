"""开发者工具 API"""
from server.services.sdk import dev_tools


def handle(body):
    action = body.get("action", "openapi")

    if action == "openapi":
        return {"ok": True, "spec": dev_tools.api_spec}

    if action == "sdk":
        return dev_tools.get_sdk_example(body.get("lang", "python"))

    if action == "cli":
        return dev_tools.get_cli_help()

    if action == "websocket":
        return dev_tools.get_websocket_info()

    return {"ok": False, "error": f"未知操作: {action}"}