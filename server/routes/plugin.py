"""插件 API 路由"""
from server.services.plugin_manager import plugin_manager


def handle(body):
    action = body.get("action", "list")
    if action == "list":
        return plugin_manager.get_plugin_list()
    if action == "toggle":
        return plugin_manager.toggle_plugin(body.get("name", ""))
    if action == "execute":
        return plugin_manager.execute_plugin(body.get("name", ""), body.get("params", {}))
    if action == "uninstall":
        return plugin_manager.uninstall_plugin(body.get("name", ""))
    return {"ok": False, "error": f"未知操作: {action}"}