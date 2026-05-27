"""
多用户会话管理
"""
import json
import os
from server.config import DATA_DIR

SESSION_DIR = os.path.join(DATA_DIR, "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

_active_sessions = {}


def create_session(username="anonymous"):
    import time, uuid
    session_id = str(uuid.uuid4())[:8]
    session = {
        "id": session_id,
        "username": username,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "history": [],
        "context": {},
    }
    _active_sessions[session_id] = session
    return session


def get_session(session_id):
    return _active_sessions.get(session_id)


def list_sessions():
    return list(_active_sessions.values())


def add_to_history(session_id, role, content):
    if session_id in _active_sessions:
        _active_sessions[session_id]["history"].append({
            "role": role,
            "content": content,
            "time": __import__('time').strftime("%H:%M:%S"),
        })


def delete_session(session_id):
    _active_sessions.pop(session_id, None)