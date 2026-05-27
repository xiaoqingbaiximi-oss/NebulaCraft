"""SDK 和 CLI 支持服务"""
import os
import json
import subprocess
from server.config import BASE_DIR


class DevTools:
    def __init__(self):
        self.api_spec = self._generate_openapi_spec()

    def _generate_openapi_spec(self):
        """生成 OpenAPI 3.0 规范"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "NebulaCraft API",
                "version": "7.0.0",
                "description": "本地全能 AI 工作站 REST API",
            },
            "servers": [{"url": "http://localhost:8889", "description": "本地服务器"}],
            "paths": {
                "/api/chat": {
                    "post": {
                        "summary": "AI 对话",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string", "description": "用户消息"},
                                            "model": {"type": "string", "default": "qwen2.5:1.5b"},
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "AI 回复"}}
                    }
                },
                "/api/calculator": {
                    "post": {
                        "summary": "计算器",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "expression": {"type": "string", "description": "计算表达式"},
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {"200": {"description": "计算结果"}}
                    }
                },
            }
        }

    def get_sdk_example(self, lang="python"):
        """生成 SDK 示例代码"""
        examples = {
            "python": '''
# NebulaCraft Python SDK
import requests

class NebulaCraft:
    def __init__(self, base_url="http://localhost:8889"):
        self.base_url = base_url

    def chat(self, message, model="qwen2.5:1.5b"):
        resp = requests.post(f"{self.base_url}/api/chat", json={
            "message": message,
            "model": model,
        })
        return resp.json()

    def calculate(self, expression):
        resp = requests.post(f"{self.base_url}/api/calculator", json={
            "expression": expression,
        })
        return resp.json()

# 使用示例
nc = NebulaCraft()
print(nc.chat("你好"))
print(nc.calculate("BMI 70 170"))
''',
            "javascript": '''
// NebulaCraft JavaScript SDK
class NebulaCraft {
    constructor(baseUrl = "http://localhost:8889") {
        this.baseUrl = baseUrl;
    }

    async chat(message, model = "qwen2.5:1.5b") {
        const resp = await fetch(`${this.baseUrl}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, model }),
        });
        return resp.json();
    }

    async calculate(expression) {
        const resp = await fetch(`${this.baseUrl}/api/calculator`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expression }),
        });
        return resp.json();
    }
}

// 使用示例
const nc = new NebulaCraft();
nc.chat("你好").then(console.log);
''',
            "curl": '''
# Curl 示例

# AI 对话
curl -X POST http://localhost:8889/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message":"你好"}'

# 计算器
curl -X POST http://localhost:8889/api/calculator \\
  -H "Content-Type: application/json" \\
  -d '{"expression":"BMI 70 170"}'

# 知识库搜索
curl -X POST http://localhost:8889/api/knowledge \\
  -H "Content-Type: application/json" \\
  -d '{"action":"search","query":"关键词"}'
''',
        }
        return {"ok": True, "lang": lang, "code": examples.get(lang, examples["python"])}

    def get_cli_help(self):
        """CLI 帮助"""
        return {
            "ok": True,
            "commands": [
                {"cmd": "nebulacraft chat '消息'", "desc": "AI 对话"},
                {"cmd": "nebulacraft calc '表达式'", "desc": "计算器"},
                {"cmd": "nebulacraft search '关键词'", "desc": "知识库搜索"},
                {"cmd": "nebulacraft export pdf", "desc": "导出对话"},
                {"cmd": "nebulacraft status", "desc": "查看状态"},
            ]
        }

    def get_websocket_info(self):
        """WebSocket 信息"""
        return {
            "ok": True,
            "ws_url": "ws://localhost:8889/ws",
            "events": ["chat_message", "tool_result", "notification"],
            "example": "const ws = new WebSocket('ws://localhost:8889/ws');"
        }


dev_tools = DevTools()