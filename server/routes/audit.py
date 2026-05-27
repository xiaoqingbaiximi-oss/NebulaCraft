"""审计日志 API"""
from server.services import audit


def handle(body):
    action = body.get("action", "query")

    if action == "query":
        return {
            "ok": True,
            "logs": audit.query(
                date=body.get("date"),
                action=body.get("filter_action"),
                user=body.get("user"),
                limit=body.get("limit", 100),
            ),
        }

    if action == "stats":
        return {"ok": True, "stats": audit.get_stats()}

    return {"ok": False, "error": f"未知操作: {action}"}