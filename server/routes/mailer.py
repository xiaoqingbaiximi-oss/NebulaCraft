"""邮件 API"""
from server.services.mailer import mailer


def handle(body):
    action = body.get("action", "status")

    if action == "status":
        return mailer.get_status()

    if action == "send":
        return mailer.send(
            to=body.get("to", ""),
            subject=body.get("subject", ""),
            body=body.get("body", ""),
        )

    return {"ok": False, "error": f"未知操作: {action}"}