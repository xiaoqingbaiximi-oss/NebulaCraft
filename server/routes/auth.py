"""简易用户系统（本地存储）"""
import os
import json
import hashlib
import secrets
from server.config import DATA_DIR

USER_FILE = os.path.join(DATA_DIR, "users.json")


def _load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def handle_register(body):
    username = body.get("username", "").strip()
    password = body.get("password", "")

    if not username or not password:
        return {"ok": False, "error": "用户名和密码不能为空"}
    if len(username) < 2:
        return {"ok": False, "error": "用户名至少2个字符"}
    if len(password) < 4:
        return {"ok": False, "error": "密码至少4个字符"}

    users = _load_users()
    if username in users:
        return {"ok": False, "error": "用户名已存在"}

    salt = secrets.token_hex(8)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    users[username] = {
        "password": pw_hash,
        "salt": salt,
        "created": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_users(users)

    return {"ok": True, "message": "注册成功"}


def handle_login(body):
    username = body.get("username", "").strip()
    password = body.get("password", "")

    users = _load_users()
    user = users.get(username)
    if not user:
        return {"ok": False, "error": "用户名不存在"}

    pw_hash = hashlib.sha256((password + user["salt"]).encode()).hexdigest()
    if pw_hash != user["password"]:
        return {"ok": False, "error": "密码错误"}

    token = secrets.token_hex(16)
    user["token"] = token
    _save_users(users)

    return {"ok": True, "token": token, "username": username}