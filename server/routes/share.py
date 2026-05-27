"""分享 API"""
import json
import os
import secrets
import time
from server.config import DATA_DIR

SHARE_DIR = os.path.join(DATA_DIR, "shares")
os.makedirs(SHARE_DIR, exist_ok=True)


def handle_create(body):
    content = body.get("content", "")
    if not content:
        return {"ok": False, "error": "内容不能为空"}

    share_id = secrets.token_hex(4)
    data = {
        "id": share_id,
        "content": content,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    filepath = os.path.join(SHARE_DIR, f"{share_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return {"ok": True, "share_id": share_id, "url": f"/share/{share_id}"}


def handle_get(share_id):
    filepath = os.path.join(SHARE_DIR, f"{share_id}.json")
    if not os.path.exists(filepath):
        return {"ok": False, "error": "分享不存在"}

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"ok": True, **data}