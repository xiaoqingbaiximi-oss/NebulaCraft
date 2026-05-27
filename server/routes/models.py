"""模型管理"""
import requests


def handle_list():
    try:
        resp = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)
        models = resp.json().get("models", [])
        return {"ok": True, "models": [{"name": m["name"], "size": str(m.get("size", ""))} for m in models]}
    except:
        return {"ok": True, "models": [
            {"name": "qwen2.5:1.5b", "size": "1.5B"},
            {"name": "qwen2.5:7b", "size": "7B"},
            {"name": "deepseek-coder:6.7b", "size": "6.7B"},
        ], "offline": True}


def handle_pull(body):
    name = body.get("model", "")
    if not name:
        return {"ok": False, "error": "请输入模型名称"}
    try:
        requests.post("http://127.0.0.1:11434/api/pull", json={"name": name}, timeout=300)
        return {"ok": True, "message": f"正在下载 {name}"}
    except:
        return {"ok": False, "error": "Ollama 未连接"}