"""笔记 API - 使用 SQLite"""
import time
from server.services import database as db


def handle(body):
    action = body.get("action", "list")
    user_id = body.get("user_id")

    if action == "list":
        notes = db.get_notes(user_id)
        return {"ok": True, "notes": notes}

    if action == "get":
        nid = body.get("id", "")
        notes = db.get_notes(user_id)
        for n in notes:
            if n["id"] == nid:
                return {"ok": True, "note": n}
        return {"ok": False, "error": "笔记不存在"}

    if action == "save":
        nid = body.get("id", str(int(time.time() * 1000)))
        title = body.get("title", "无标题")
        content = body.get("content", "")
        db.save_note(nid, title, content, user_id)
        return {"ok": True, "id": nid}

    if action == "delete":
        nid = body.get("id", "")
        db.delete_note(nid)
        return {"ok": True}

    return {"ok": False, "error": "未知操作"}