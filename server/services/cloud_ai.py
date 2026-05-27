"""云端模型代理 - 本地模型不够时自动切换云端"""
import os
import json
import requests
from server.config import DEFAULT_MODEL


class CloudAI:
    def __init__(self):
        self.providers = {
            "openai": {
                "url": "https://api.openai.com/v1/chat/completions",
                "key": os.environ.get("OPENAI_API_KEY", ""),
                "model": "gpt-4o-mini",
            },
            "deepseek": {
                "url": "https://api.deepseek.com/v1/chat/completions",
                "key": os.environ.get("DEEPSEEK_API_KEY", ""),
                "model": "deepseek-chat",
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.environ.get("GROQ_API_KEY", ""),
                "model": "llama-3.3-70b-versatile",
            },
        }
        self.enabled = False
        self.current = None
        self._detect()

    def _detect(self):
        """检测可用的云端服务"""
        for name, cfg in self.providers.items():
            if cfg["key"]:
                self.enabled = True
                if not self.current:
                    self.current = name
                    print(f"☁️ 云端模型可用: {name} ({cfg['model']})")

    def chat(self, messages, provider=None):
        """使用云端模型对话"""
        p = provider or self.current
        if not p or p not in self.providers:
            return None

        cfg = self.providers[p]
        if not cfg["key"]:
            return None

        try:
            resp = requests.post(
                cfg["url"],
                headers={
                    "Authorization": f"Bearer {cfg['key']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": cfg["model"],
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            return f"云端错误: {resp.status_code}"
        except Exception as e:
            return None

    def get_status(self):
        providers_status = {}
        for name, cfg in self.providers.items():
            providers_status[name] = {
                "available": bool(cfg["key"]),
                "model": cfg["model"],
            }
        return {
            "ok": True,
            "enabled": self.enabled,
            "current": self.current,
            "providers": providers_status,
            "tip": "设置环境变量启用云端模型: OPENAI_API_KEY / DEEPSEEK_API_KEY / GROQ_API_KEY",
        }


cloud_ai = CloudAI()