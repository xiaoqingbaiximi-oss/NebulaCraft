"""
协作 API
"""
from server.services.multi_user import create_session, get_session, list_sessions, add_to_history, delete_session


def handle(body: dict) -> dict:
    action = body.get("action", "create")

    if action == "create":
        s = create_session(body.get("username", "anonymous"))
        return {"ok": True, "session": s}
    if action == "get":
        s = get_session(body.get("session_id", ""))
        return {"ok": True, "session": s} if s else {"ok": False, "error": "Session not found"}
    if action == "list":
        return {"ok": True, "sessions": list_sessions()}
    if action == "delete":
        delete_session(body.get("session_id", ""))
        return {"ok": True}
    if action == "add_history":
        add_to_history(body.get("session_id", ""), body.get("role", ""), body.get("content", ""))
        return {"ok": True}

    return {"ok": False, "error": "Unknown action"}