# -*- coding: utf-8 -*-
"""
对话 API
"""
import json
from server.services.ollama import chat, chat_stream, is_available
from server.services.search_web import search as web_search
from server.config import DEFAULT_MODEL

_sessions = {}
MAX_HISTORY = 20


def _get_history(session_id: str) -> list:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def _add_to_history(session_id: str, role: str, content: str):
    history = _get_history(session_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        _sessions[session_id] = history[-MAX_HISTORY * 2:]


def handle(body: dict) -> dict:
    prompt = body.get("message", "").strip()
    model = body.get("model", DEFAULT_MODEL)
    session_id = body.get("session_id", "default")

    if not prompt:
        return {"ok": False, "error": "消息不能为空"}

    messages = [{"role": "user", "content": prompt}]
    reply = chat(messages, model, timeout=120)

    return {
        "ok": True,
        "reply": reply,
        "source": "ai",
        "references": [],
        "session_id": session_id,
    }


def handle_search(body: dict) -> dict:
    prompt = body.get("message", "").strip()
    if not prompt:
        return {"ok": False, "error": "请输入搜索内容"}
    results = web_search(prompt)
    return {"ok": True, "reply": str(results)[:500], "source": "search", "references": results[:5] if results else []}


def handle_stream(body: dict):
    prompt = body.get("message", "").strip()
    model = body.get("model", DEFAULT_MODEL)

    if not prompt:
        return lambda: iter(["data: " + json.dumps({"error": "消息不能为空"}) + "\n\n"])

    def gen():
        full_reply = ""
        try:
            for chunk in chat_stream([{"role": "user", "content": prompt}], model):
                full_reply += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return gen