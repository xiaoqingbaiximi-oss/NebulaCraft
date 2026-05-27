"""配额 API"""
from server.services import quota


def handle(body):
    action = body.get("action", "check")
    user = body.get("user", "default")

    if action == "check":
        return {"ok": True, "quota": quota.check_quota(user)}

    if action == "usage":
        return {"ok": True, "usage": quota.get_usage(user)}

    return {"ok": False, "error": f"未知操作: {action}"}