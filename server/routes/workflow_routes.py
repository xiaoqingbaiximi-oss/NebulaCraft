"""
工作流 API
"""
from server.services.workflow import add_workflow, list_workflows, delete_workflow, run_workflow_now, execute_workflow


def handle(body: dict) -> dict:
    action = body.get("action", "list")

    if action == "add":
        return add_workflow(
            name=body.get("name", ""),
            trigger=body.get("trigger", {}),
            nodes=body.get("nodes", []),
        )
    if action == "list":
        return list_workflows()
    if action == "delete":
        return delete_workflow(body.get("id", ""))
    if action == "run":
        return run_workflow_now(body.get("id", ""))
    if action == "execute":
        return execute_workflow(body.get("workflow", {}))

    return {"ok": False, "error": "Unknown action"}