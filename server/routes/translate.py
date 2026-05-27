"""翻译 API"""
import requests
from server.config import OLLAMA_CHAT, DEFAULT_MODEL


def handle(body):
    text = body.get("text", "").strip()
    target = body.get("target", "中文")

    if not text:
        return {"ok": False, "error": "请输入要翻译的文字"}

    prompt = f"请将以下内容翻译为{target}，只输出译文，不要解释：\n{text}"

    try:
        resp = requests.post(
            OLLAMA_CHAT,
            json={
                "model": DEFAULT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=60,
        )
        result = resp.json().get("message", {}).get("content", "")
        return {"ok": True, "result": result.strip(), "target": target}
    except Exception as e:
        return {"ok": False, "error": f"翻译失败: {e}"}