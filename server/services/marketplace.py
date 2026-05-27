"""
插件市场服务
支持: 浏览 / 安装 / 卸载插件
"""
import os
import json
import shutil
import zipfile
import tempfile
import urllib.request
from server.config import DATA_DIR

PLUGIN_DIR = os.path.join(DATA_DIR, "plugins")
MARKETPLACE_FILE = os.path.join(DATA_DIR, "marketplace.json")
os.makedirs(PLUGIN_DIR, exist_ok=True)

# 默认插件市场数据
DEFAULT_MARKETPLACE = {
    "plugins": [
        {
            "id": "hello_world",
            "name": "Hello World",
            "version": "1.0.0",
            "description": "示例插件，展示基本插件结构",
            "author": "NebulaCraft",
            "icon": "👋",
            "category": "示例",
            "installed": True,
            "download_url": "",
        },
        {
            "id": "code_formatter",
            "name": "代码格式化",
            "version": "1.0.0",
            "description": "自动格式化代码，支持 Python/JS/JSON",
            "author": "NebulaCraft",
            "icon": "📝",
            "category": "开发工具",
            "installed": False,
            "download_url": "",
        },
        {
            "id": "daily_report",
            "name": "日报生成器",
            "version": "1.0.0",
            "description": "根据工作日志自动生成日报/周报",
            "author": "NebulaCraft",
            "icon": "📊",
            "category": "办公",
            "installed": False,
            "download_url": "",
        },
        {
            "id": "meme_generator",
            "name": "表情包生成器",
            "version": "1.0.0",
            "description": "AI 生成搞笑表情包",
            "author": "NebulaCraft",
            "icon": "😂",
            "category": "娱乐",
            "installed": False,
            "download_url": "",
        },
        {
            "id": "sql_helper",
            "name": "SQL 助手",
            "version": "1.0.0",
            "description": "自然语言转 SQL，数据库查询优化",
            "author": "NebulaCraft",
            "icon": "🗄️",
            "category": "开发工具",
            "installed": False,
            "download_url": "",
        },
    ]
}


def _load_marketplace():
    if os.path.exists(MARKETPLACE_FILE):
        try:
            with open(MARKETPLACE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    _save_marketplace(DEFAULT_MARKETPLACE)
    return DEFAULT_MARKETPLACE


def _save_marketplace(data):
    with open(MARKETPLACE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_installed_plugins():
    """获取已安装插件列表"""
    installed = []
    if os.path.exists(PLUGIN_DIR):
        for d in os.listdir(PLUGIN_DIR):
            manifest_path = os.path.join(PLUGIN_DIR, d, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    installed.append(manifest.get("name", d))
                except:
                    installed.append(d)
    return installed


def list_plugins(category=""):
    """列出所有可用插件"""
    marketplace = _load_marketplace()
    installed = _get_installed_plugins()

    plugins = marketplace.get("plugins", [])
    for p in plugins:
        p["installed"] = p["id"] in installed or p.get("name") in installed

    if category:
        plugins = [p for p in plugins if p.get("category", "") == category]

    return {"ok": True, "plugins": plugins, "total": len(plugins)}


def install_plugin(plugin_id):
    """安装插件"""
    marketplace = _load_marketplace()
    plugin = None
    for p in marketplace.get("plugins", []):
        if p["id"] == plugin_id:
            plugin = p
            break

    if not plugin:
        return {"ok": False, "error": f"插件 {plugin_id} 不存在"}

    # 创建插件目录
    plugin_path = os.path.join(PLUGIN_DIR, plugin_id)
    os.makedirs(plugin_path, exist_ok=True)

    # 生成插件主体
    main_code = f'''"""
{plugin["name"]} - {plugin["description"]}
Author: {plugin["author"]}
Version: {plugin["version"]}
"""
class Plugin:
    def __init__(self):
        self.name = "{plugin["name"]}"
        self.version = "{plugin["version"]}"

    def on_load(self):
        print("[Plugin] {plugin["name"]} loaded")
        return True

    def on_unload(self):
        print("[Plugin] {plugin["name"]} unloaded")
        return True

    def execute(self, params):
        prompt = params.get("message", "")
        from server.services.ollama import chat
        result = chat([{{"role": "user", "content": f"[{plugin["name"]}] {{prompt}}"}}])
        return {{"ok": True, "result": result}}
'''

    with open(os.path.join(plugin_path, "main.py"), "w", encoding="utf-8") as f:
        f.write(main_code)

    # 生成 manifest
    manifest = {
        "name": plugin["name"],
        "version": plugin["version"],
        "description": plugin["description"],
        "author": plugin["author"],
        "entry": "main",
        "enabled": True,
    }
    with open(os.path.join(plugin_path, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 更新市场状态
    for p in marketplace["plugins"]:
        if p["id"] == plugin_id:
            p["installed"] = True
    _save_marketplace(marketplace)

    return {"ok": True, "message": f"插件 {plugin['name']} 安装成功！重启后生效"}


def uninstall_plugin(plugin_id):
    """卸载插件"""
    marketplace = _load_marketplace()
    plugin_path = os.path.join(PLUGIN_DIR, plugin_id)

    if os.path.exists(plugin_path):
        shutil.rmtree(plugin_path)

    for p in marketplace["plugins"]:
        if p["id"] == plugin_id:
            p["installed"] = False
    _save_marketplace(marketplace)

    return {"ok": True, "message": f"插件 {plugin_id} 已卸载"}