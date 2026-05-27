"""
插件市场 API
"""
from server.services.marketplace import list_plugins, install_plugin, uninstall_plugin


def handle(body: dict) -> dict:
    action = body.get("action", "list")

    if action == "list":
        return list_plugins(body.get("category", ""))
    if action == "install":
        return install_plugin(body.get("plugin_id", ""))
    if action == "uninstall":
        return uninstall_plugin(body.get("plugin_id", ""))

    return {"ok": False, "error": f"未知操作: {action}"}