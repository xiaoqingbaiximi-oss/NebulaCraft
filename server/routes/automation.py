"""自动化 API"""
from server.services.automation import automation


def handle(body):
    action = body.get("action", "list")

    if action == "list":
        return automation.list_workflows()

    if action == "create":
        return automation.create_workflow(
            body.get("name", ""),
            body.get("steps", []),
            body.get("trigger"),
        )

    if action == "execute":
        return automation.execute_workflow(body.get("id", ""))

    if action == "delete":
        return automation.delete_workflow(body.get("id", ""))

    return {"ok": False, "error": f"未知操作: {action}"}