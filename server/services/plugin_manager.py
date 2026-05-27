"""
插件管理器
"""
import os
import json
import sys
import importlib
import traceback
from server.config import DATA_DIR

PLUGIN_DIR = os.path.join(DATA_DIR, "plugins")
os.makedirs(PLUGIN_DIR, exist_ok=True)


class PluginManager:
    def __init__(self):
        self.plugins = {}
        self._load_all()
    
    def _load_all(self):
        if not os.path.exists(PLUGIN_DIR):
            return
        for folder in os.listdir(PLUGIN_DIR):
            plugin_path = os.path.join(PLUGIN_DIR, folder)
            if not os.path.isdir(plugin_path):
                continue
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    sys.path.insert(0, plugin_path)
                    module = importlib.import_module(manifest.get("entry", "main"))
                    plugin_instance = module.Plugin() if hasattr(module, "Plugin") else module
                    self.plugins[manifest["name"]] = {
                        "manifest": manifest,
                        "module": module,
                        "instance": plugin_instance,
                        "path": plugin_path,
                        "enabled": True,
                    }
                    if hasattr(plugin_instance, "on_load"):
                        plugin_instance.on_load()
                    print(f"✅ 插件已加载: {manifest['name']} v{manifest.get('version', '1.0')}")
                except Exception as e:
                    print(f"❌ 插件加载失败: {folder} - {e}")
    
    def get_plugin_list(self):
        plugins = []
        for name, p in self.plugins.items():
            m = p["manifest"]
            plugins.append({"name": name, "version": m.get("version", "1.0"), "description": m.get("description", ""), "author": m.get("author", ""), "enabled": p["enabled"]})
        return {"ok": True, "plugins": sorted(plugins, key=lambda x: x["name"])}
    
    def toggle_plugin(self, name):
        if name not in self.plugins:
            return {"ok": False, "error": "插件不存在"}
        self.plugins[name]["enabled"] = not self.plugins[name]["enabled"]
        status = "已启用" if self.plugins[name]["enabled"] else "已禁用"
        return {"ok": True, "message": f"插件「{name}」{status}", "enabled": self.plugins[name]["enabled"]}
    
    def execute_plugin(self, name, params):
        if name not in self.plugins:
            return {"ok": False, "error": "插件不存在"}
        p = self.plugins[name]
        if not p["enabled"]:
            return {"ok": False, "error": "插件已禁用"}
        try:
            if hasattr(p["instance"], "execute"):
                return p["instance"].execute(params)
            return {"ok": False, "error": "插件未实现 execute 方法"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def uninstall_plugin(self, name):
        if name not in self.plugins:
            return {"ok": False, "error": "插件不存在"}
        import shutil
        if os.path.exists(self.plugins[name]["path"]):
            shutil.rmtree(self.plugins[name]["path"])
        del self.plugins[name]
        return {"ok": True, "message": f"插件「{name}」已卸载"}


plugin_manager = PluginManager()